import synapseclient as sc
import numpy as np
import pandas as pd
import os
import glob
import argparse
from itertools import product
import logging

# logging config
logging.basicConfig(format="%(asctime)s %(message)s")
logger = logging.getLogger("defaultLogger")
logger.setLevel(logging.INFO)

# global constants
TEST_SUBMISSION_PATH = "testSubmissions"


def readargs():
    """Read in command line arguments.

    Returns
    -------
    args : dict
        contains arguments passed.
    """
    parser = argparse.ArgumentParser(
        description="Make test submissions to a \
            Synapse Evaluation queue"
    )
    parser.add_argument(
        "--synProject",
        help="Synapse project where test \
            submissions generated by script should be located.",
    )
    parser.add_argument(
        "--indexCols",
        metavar="i",
        help="Comma \
            seperated list of columns required to be in submission \
            (defaults to first column of sampleSubmission).",
    )
    parser.add_argument("--filetype", help="csv or tsv")
    parser.add_argument(
        "evaluationQueue", type=int, help="ID of Synapse Evaluation"
    )
    parser.add_argument(
        "sampleSubmission",
        type=str,
        help="A .csv or .tsv file \
            which is known to pass all test cases.",
    )
    args = parser.parse_args()
    return args


def writeSubmissions(sampleSubmission, indexCols=None, filetype="csv"):
    """Write a number of submissions to the path indicated by TEST_SUBMISSION_PATH.

    Arguments
    ---------
    sampleSubmission : str
        path to submission file that is known to pass tests.
    indexCols : list-like
        Columns which are required to be in submissions file
        (default first col of sampleSubmission).
    filetype : str
        filename extension to append to filenames (default 'csv').

    Returns
    -------
    None
    """
    sample = pd.read_csv(
        sampleSubmission, sep=None, engine="python", index_col=indexCols
    )
    if not indexCols:  # default index is first column
        sample = sample.set_index(sample.columns[0], drop=True)
    sample_index = sample.index
    delimiter = "," if filetype == "csv" else "\t"
    # write test submissions to file
    logger.info(
        "Writing submissions to {} in .{} format".format(
            TEST_SUBMISSION_PATH, filetype
        )
    )
    # a single blank space
    with open(
        "{}/blankSpace.{}".format(TEST_SUBMISSION_PATH, filetype), "w"
    ) as f:
        f.write(" ")
    # random binary file
    with open(
        "{}/randomBinary.{}".format(TEST_SUBMISSION_PATH, filetype), "wb"
    ) as f:
        f.write(os.urandom(1024))
    # only required columns
    pd.DataFrame({}, index=sample_index).to_csv(
        "{}/onlyIndexCols.{}".format(TEST_SUBMISSION_PATH, filetype),
        index=True,
        sep=delimiter,
    )
    # only required columns with quoting
    pd.DataFrame({}, index=sample_index).to_csv(
        "{}/onlyIndexColsWithQuoting.{}".format(
            TEST_SUBMISSION_PATH, filetype
        ),
        index=True,
        quoting=1,
        sep=delimiter,
    )
    # only required columns with trailing comma
    with open(
        "{}/onlyIndexCols.{}".format(TEST_SUBMISSION_PATH, filetype), "r"
    ) as f:
        result = "\n".join(["%s," % l for l in f.read().split("\n")])
        with open(
            "{}/onlyIndexColsWithTrailingComma.{}".format(
                TEST_SUBMISSION_PATH, filetype
            ),
            "w",
        ) as output:
            output.write(result)
    # wrong delimiter
    sample.to_csv(
        "{}/wrongDelimiter.{}".format(TEST_SUBMISSION_PATH, filetype), sep=" "
    )
    # duplicated indices
    sample.append(sample.iloc[0]).to_csv(
        "{}/duplicateIndices.{}".format(TEST_SUBMISSION_PATH, filetype),
        sep=delimiter,
    )
    # infinite values
    sample_copy = sample.copy()
    sample_copy.iloc[0, 0] = float("inf")
    sample_copy.to_csv(
        "{}/infiniteValue.{}".format(TEST_SUBMISSION_PATH, filetype),
        index=True,
        sep=delimiter,
    )
    # a REALLY BIG (but less than infinite) value
    sample_copy.iloc[0, 0] = 2e64
    sample_copy.to_csv(
        "{}/reallyBigValue.{}".format(TEST_SUBMISSION_PATH, filetype),
        index=True,
        sep=delimiter,
    )
    # one, two, and five columns of random floats, ints, strings with/without NAs
    for i, t, na in product([1, 2, 5], [float, int, str], [True, False]):
        cases = {float: "float", int: "int", str: "str"}
        if t == int or t == float:
            raw_df = {
                "col{}".format(j): list(
                    map(
                        t,
                        np.random.randint(10, size=len(sample_index))
                        + np.random.randn(len(sample_index)),
                    )
                )
                for j in range(i)
            }
        elif t == str:
            raw_df = {
                "col{}".format(j): list(
                    map(chr, np.random.randint(41, 123, len(sample_index)))
                )
                for j in range(i)
            }
        if na:
            raw_df["col0"][0] = float("nan")
        df = pd.DataFrame(raw_df, index=sample_index)
        df.to_csv(
            "{}/{}Col_{}_na{}.{}".format(
                TEST_SUBMISSION_PATH, i, cases[t], na, filetype
            ),
            index=True,
            header=True,
            sep=delimiter,
        )


def storeSubmissions(syn, evaluationQueue, synProject=None, filetype="csv"):
    """Store submissions on Synapse and submit to the evaluation queue.

    Arguments
    ---------
    syn : synapseclient.Synapse
    evaluationQueue : int
        Evaluation ID.
    synProject : str
        Synapse ID of project to store files to.
    filetype : str
        filename extension to append to filenames (default 'csv').

    Returns
    -------
    None
    """
    if not synProject:
        logger.info("Creating new Synapse Project")
        user_profile = syn.getUserProfile()
        project_name = "{}_{}_testSubmissions".format(
            user_profile["userName"], evaluationQueue
        )
        synProject = sc.Project(project_name)
        synProject = syn.store(synProject).id
        logger.info("Synapse project created at {}".format(synProject))
    for submission in glob.glob(
        "{}/*.{}".format(TEST_SUBMISSION_PATH, filetype)
    ):
        logger.info(
            "Storing {} to {} and submitting to {}".format(
                submission, synProject, evaluationQueue
            )
        )
        synFile = sc.File(submission, parent=synProject)
        synFile = syn.store(synFile)
        syn.submit(evaluationQueue, synFile, name=os.path.basename(submission))


def main():
    if not os.path.exists(TEST_SUBMISSION_PATH):
        os.makedirs(TEST_SUBMISSION_PATH)
    syn = sc.login()
    args = readargs()
    args.filetype = "csv" if not args.filetype else args.filetype
    indexCols = None if not args.indexCols else args.indexCols.split(",")
    writeSubmissions(args.sampleSubmission, indexCols, args.filetype)
    storeSubmissions(syn, args.evaluationQueue, args.synProject, args.filetype)
    logger.info("Finished")


if __name__ == "__main__":
    main()
