"""Test script for RAG system."""
from rag_vector_db import initialize_rag_db
from google_drive_mcp import initialize_google_drive


def test_google_drive():
    """Test Google Drive connection."""
    print("\n Testing Google Drive Connection\n")

    try:
        drive = initialize_google_drive()
        if not drive:
            print("[FAIL] Google Drive not available")
            return False

        print("[OK] Google Drive connection OK")
        return True
    except Exception as e:
        print(f"[FAIL] Google Drive error: {e}")
        return False


def test_vector_db():
    """Test vector database."""
    print("\n Testing Vector Database\n")

    try:
        rag_db = initialize_rag_db()
        stats = rag_db.get_db_stats()

        print(f"[OK] Vector DB initialized")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Location: {stats.get('persist_dir', '.vector_db')}")

        if stats.get('total_chunks', 0) == 0:
            print("[WARN]  No data in vector database - run: python load_rag_data.py")

        return True
    except Exception as e:
        print(f"[FAIL] Vector DB error: {e}")
        return False


def test_retrieval(query: str = "doctor availability"):
    """Test document retrieval."""
    print(f"\n Testing Document Retrieval\n")
    print(f"Query: '{query}'")

    try:
        rag_db = initialize_rag_db()
        results = rag_db.retrieve_relevant_context(query, top_k=3)

        if not results:
            print("[WARN]  No results found - database may be empty")
            return False

        print(f"[OK] Retrieved {len(results)} documents")
        for i, result in enumerate(results, 1):
            preview = result[:100].replace("\n", " ") + "..."
            print(f"\n   [{i}] {preview}")

        return True
    except Exception as e:
        print(f"[FAIL] Retrieval error: {e}")
        return False


def test_doctor_lookup(doctor_name: str = "Dr. Willi Bedna"):
    """Test doctor-specific lookup."""
    print(f"\n Testing Doctor Lookup\n")
    print(f"Doctor: {doctor_name}")

    try:
        rag_db = initialize_rag_db()
        info = rag_db.get_doctor_info(doctor_name)

        if not info:
            print(f"[WARN]  No information found for {doctor_name}")
            return False

        preview = info[:150].replace("\n", " ") + "..."
        print(f"[OK] Found doctor information")
        print(f"   {preview}")

        return True
    except Exception as e:
        print(f"[FAIL] Doctor lookup error: {e}")
        return False


def test_patient_lookup(patient_name: str = "John Doe"):
    """Test patient-specific lookup."""
    print(f"\n Testing Patient Lookup\n")
    print(f"Patient: {patient_name}")

    try:
        rag_db = initialize_rag_db()
        info = rag_db.get_patient_info(patient_name)

        if not info:
            print(f"[WARN]  No information found for {patient_name}")
            return False

        preview = info[:150].replace("\n", " ") + "..."
        print(f"[OK] Found patient information")
        print(f"   {preview}")

        return True
    except Exception as e:
        print(f"[FAIL] Patient lookup error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("   MedAssistAI RAG System Tests")
    print("=" * 50)

    tests = [
        ("Google Drive", test_google_drive),
        ("Vector Database", test_vector_db),
        ("Document Retrieval", test_retrieval),
        ("Doctor Lookup", test_doctor_lookup),
        ("Patient Lookup", test_patient_lookup),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n[FAIL] {test_name} failed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 50)
    print("   Test Summary")
    print("=" * 50)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_test in results.items():
        status = "[OK] PASS" if passed_test else "[FAIL] FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n[WARN]  {total - passed} test(s) failed")
        print("See troubleshooting in RAG_SETUP.md")

    print()


if __name__ == "__main__":
    main()
