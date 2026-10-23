from app.blockchain.chain import GENESIS_PREVIOUS_HASH, compute_hash, genesis_block, make_block, validate_chain


def _chain(n=3):
    blocks = [genesis_block()]
    for i in range(n):
        blocks.append(make_block(len(blocks), blocks[-1]["block_hash"], {"type": "approved_topic", "topic_title": f"Topic {i}"}))
    return blocks


def test_genesis_links_to_zero_hash():
    assert genesis_block()["previous_hash"] == GENESIS_PREVIOUS_HASH


def test_untouched_chain_is_valid():
    assert validate_chain(_chain())["valid"] is True


def test_data_edit_is_detected():
    c = _chain()
    c[2]["data"] = c[2]["data"].replace("Topic 1", "Hacked")
    r = validate_chain(c)
    assert not r["valid"] and r["broken_at_index"] == 2 and r["reason"].startswith("hash_mismatch")


def test_recomputed_hash_breaks_next_link():
    c = _chain()
    c[2]["data"] = c[2]["data"].replace("Topic 1", "Hacked")
    c[2]["block_hash"] = compute_hash(2, c[2]["timestamp"], c[2]["data"], c[2]["previous_hash"])
    r = validate_chain(c)
    assert not r["valid"] and r["broken_at_index"] == 3 and r["reason"].startswith("link_broken")


def test_deleted_block_is_detected():
    c = _chain()
    del c[1]
    assert not validate_chain(c)["valid"]


def test_same_data_gives_same_hash():
    a = make_block(1, "x", {"b": 1, "a": 2}, timestamp="t")
    b = make_block(1, "x", {"a": 2, "b": 1}, timestamp="t")
    assert a["block_hash"] == b["block_hash"]
