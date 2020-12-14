import pytest


def test_categorical_encoder():
    from speechbrain.data_io.encoder import CategoricalEncoder

    encoder = CategoricalEncoder()
    encoder.update_from_iterable("abcd")
    integers = encoder.encode_sequence("dcba")
    assert all(isinstance(i, int) for i in integers)
    assert encoder.is_continuous()
    with pytest.raises(KeyError):
        encoder.add_label("a")
    # Does NOT raise:
    encoder.ensure_label("a")
    with pytest.raises(KeyError):
        encoder.insert_label("a", -3)
    encoder.enforce_label("a", -3)
    assert encoder.encode_label("a") == -3
    assert not encoder.is_continuous()

    # Decoding:
    import torch

    encoder = CategoricalEncoder()
    encoder.update_from_iterable("abcd")
    result = encoder.decode_torch(
        torch.tensor([[0, 0], [1, 1], [2, 2], [3, 3]])
    )
    assert result == [["a", "a"], ["b", "b"], ["c", "c"], ["d", "d"]]
    result = encoder.decode_ndim([[0, 0], [1, 1], [2, 2], [3, 3]])
    assert result == [["a", "a"], ["b", "b"], ["c", "c"], ["d", "d"]]
    result = encoder.decode_ndim(torch.tensor([[0, 0], [1, 1], [2, 2], [3, 3]]))
    assert result == [["a", "a"], ["b", "b"], ["c", "c"], ["d", "d"]]
    result = encoder.decode_ndim([[[[[0, 0], [1, 1], [2, 2], [3, 3]]]]])
    assert result == [[[[["a", "a"], ["b", "b"], ["c", "c"], ["d", "d"]]]]]
    result = encoder.decode_torch(
        torch.tensor([[[[[0, 0], [1, 1], [2, 2], [3, 3]]]]])
    )
    assert result == [[[[["a", "a"], ["b", "b"], ["c", "c"], ["d", "d"]]]]]
    result = encoder.decode_ndim([[0, 0], [1], [2, 2, 2], []])
    assert result == [["a", "a"], ["b"], ["c", "c", "c"], []]

    encoder = CategoricalEncoder()
    encoder.limited_labelset_from_iterable("aabbbcccd", n_most_common=3)
    encoder.encode_sequence("abc")
    with pytest.raises(KeyError):
        encoder.encode_label("d")
    encoder = CategoricalEncoder()
    encoder.limited_labelset_from_iterable("aabbbcccd", min_count=3)
    encoder.encode_sequence("cbcb")
    with pytest.raises(KeyError):
        encoder.encode_label("a")
    with pytest.raises(KeyError):
        encoder.encode_label("d")
    encoder = CategoricalEncoder()
    encoder.limited_labelset_from_iterable(
        "aabbbcccd", n_most_common=3, min_count=3
    )
    encoder.encode_sequence("cbcb")
    with pytest.raises(KeyError):
        encoder.encode_label("a")
    with pytest.raises(KeyError):
        encoder.encode_label("d")


def test_categorical_encoder_saving(tmpdir):
    from speechbrain.data_io.encoder import CategoricalEncoder

    encoder = CategoricalEncoder(starting_index=3)
    encoding_file = tmpdir / "char_encoding.txt"
    # First time this runs, the encoding is created:
    if not encoder.load_if_possible(encoding_file):
        encoder.update_from_iterable("abcd")
        encoder.save(encoding_file)
    else:
        assert False  # We should not get here!
    # Now, imagine a recovery:
    encoder = CategoricalEncoder()
    # The second time, the encoding is just loaded from file:
    if not encoder.load_if_possible(encoding_file):
        assert False  # We should not get here!
    integers = encoder.encode_sequence("dcba")
    assert all(isinstance(i, int) for i in integers)
    assert encoder.starting_index == 3  # This is also loaded

    # Also possible to encode tuples and load
    encoder = CategoricalEncoder()
    encoding_file = tmpdir / "tuple_encoding.txt"
    encoder.add_label((1, 2, 3))
    encoder.insert_label((1, 2), index=-1)
    encoder.save(encoding_file)
    # Reload
    encoder = CategoricalEncoder()
    assert encoder.load_if_possible(encoding_file)
    assert encoder.encode_label((1, 2)) == -1


def test_categorical_encoder_from_dataset():
    from speechbrain.data_io.encoder import CategoricalEncoder
    from speechbrain.data_io.dataset import DynamicItemDataset

    encoder = CategoricalEncoder()
    data = {
        "utt1": {"foo": -1, "bar": 0, "text": "hello world"},
        "utt2": {"foo": 1, "bar": 2, "text": "how are you world"},
        "utt3": {"foo": 3, "bar": 4, "text": "where are you world"},
        "utt4": {"foo": 5, "bar": 6, "text": "hello nation"},
    }
    dynamic_items = {
        "words": {"func": lambda x: x.split(), "argkeys": ["text"]},
        "words_t": {"func": encoder.encode_sequence, "argkeys": ["words"]},
    }
    output_keys = ["words_t"]
    dataset = DynamicItemDataset(data, dynamic_items, output_keys)
    encoder.update_from_didataset(dataset, "words", sequence_input=True)
    assert dataset[0]["words_t"] == [0, 1]
    assert encoder.decode_ndim(dataset[0]["words_t"]) == ["hello", "world"]
