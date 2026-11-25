import test_workflow
import pytest

def test_tocomo_session(driver):

    # create and strat session
        # create and strat transaction
        # collect app startup data
                test_workflow.sample_test(driver)
        # stop transaction

        # create and strat transaction
        # collect memory info
        # collect gfx info
                test_workflow.sample_test(driver)
        # stop transaction

        # create and strat parent transaction
        # collect memory info
        # collect gfx info
            # create and strat transaction
            # collect Battery stats
                test_workflow.sample_test(driver)
            # stop transaction
        #stop  parent transaction

    #stop Session
def test_tocomo_lone_transaction(driver):
    # create and strat loop transaction for i > 10
    #collect cpu info
                test_workflow.sample_test(driver)
    # stop loop transaction




