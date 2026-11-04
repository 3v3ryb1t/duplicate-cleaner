import allure

from duplicate_cleaner.duplicate_cleaner import remove_duplicate_files

from .assertions import assert_bool_result


@allure.epic("Cleanup")
@allure.feature("Files Deletion")
@allure.title("Deleting a duplicateУдаление дубликата - symbolic link")
@allure.story("Collapsing symbolic links chains")
@allure.severity(allure.severity_level.CRITICAL)
def test_remove_duplicate_as_symlink(create_test_tree):
    with allure.step("Generating original file, a duplciate and a link to it"):
        structure = {
            "original.txt": "data",
            "duplicate.txt": "data",
            "link_to_duplicate.txt": "symlink:duplicate.txt",
        }
        test_path = create_test_tree(structure)

        duplicates = {
            "hash_data": [
                test_path / "original.txt",
                test_path / "link_to_duplicate.txt",
            ]
        }

    with allure.step("Deleting duplicate which is a symbolic link"):
        remove_duplicate_files(duplicates)

    assert_bool_result(
        expected=True,
        f=lambda: (test_path / "original.txt").exists(),
        step="Checking original file is untouched",
    )

    assert_bool_result(
        expected=False,
        f=lambda: (test_path / "link_to_duplicate.txt").exists(),
        step="Checking duplicate file is removed",
    )
