from app.services.policy_retriever import retrieve_policy


def test_hotel_policy_is_top_result():
    results = retrieve_policy("domestic hotel reimbursement")
    assert results
    assert results[0]["section"] == "HOTEL-01"


def test_taxi_policy_is_top_result():
    results = retrieve_policy("airport cab taxi business travel")
    assert results
    assert results[0]["section"] == "TAXI-01"
