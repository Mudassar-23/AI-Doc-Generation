import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runner.tests.test_pipeline import (
    db_session,
    test_fallback_provider_sequence,
    test_clone_repository_and_cleanup,
    test_stage_manager_pipeline,
    test_chunking_and_file_filters,
)


class MockTmpPath:
    def __init__(self, path):
        self.path = path

    def __div__(self, other):
        return MockTmpPath(os.path.join(self.path, other))

    def __truediv__(self, other):
        return MockTmpPath(os.path.join(self.path, other))

    def __str__(self):
        return self.path


def main():
    print("=" * 60)
    print("Running Custom Test Suite...")
    print("=" * 60)

    # Create a local test temporary directory
    test_tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp_tests")
    if os.path.exists(test_tmp_dir):
        import shutil
        shutil.rmtree(test_tmp_dir, ignore_errors=True)
    os.makedirs(test_tmp_dir, exist_ok=True)

    tmp_path = MockTmpPath(test_tmp_dir)

    try:
        print("[1/3] Testing FallbackProvider sequence...")
        test_fallback_provider_sequence()
        print("=> SUCCESS!")

        print("[2/3] Testing clone_repository with absolute paths...")
        test_clone_repository_and_cleanup(tmp_path)
        print("=> SUCCESS!")

        print("[3/4] Testing StageManager pipeline end-to-end...")
        session_gen = db_session()
        session = next(session_gen)
        test_stage_manager_pipeline(session, tmp_path)
        print("=> SUCCESS!")

        print("[4/4] Testing Chunking & File Filter rules (4K/5K tokens, 3MB skip, 700KB chunk, non-truncation)...")
        test_chunking_and_file_filters(tmp_path)
        print("=> SUCCESS!")


        print("=" * 60)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
    except Exception as e:
        print("\n!!! TEST SUITE FAILED !!!")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up temporary test directories
        try:
            from runner.stages.s1_clone import safe_rmtree
            safe_rmtree(test_tmp_dir)
        except Exception:
            pass


if __name__ == "__main__":
    main()
