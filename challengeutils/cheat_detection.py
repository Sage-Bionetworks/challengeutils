
## calculations
import pandas as pd 
import numpy as np
from tabulate import tabulate
from synapseclient import Synapse
import jellyfish as j
from scipy.spatial.distance import pdist as p
import json
import copy


class CheatDetection:

    def __init__(self, syn: Synapse, evaluation_id: int):
        self.syn = syn
        
        self.linked_users = pd.DataFrame()

        self.user_clusters = pd.DataFrame()

        self.accepted_submissions = []

        self.evaluation = evaluation_id

        #self.rounds = self.get_evaluation_rounds()
    


    def __str__(self):
        """String representation"""

        output = f"""
Evaluation ID: {self.evaluation}
Accepted Submissions: {len(self.accepted_submissions)}
Potentially Linked Users: {self.get_number_of_linked_users()}
        """

        return output



    def __repr__(self):
        """Repr() representation"""

        rep = f"CheatDetection({self.syn}, {self.evaluation})"

        return rep
    


    def get_number_of_linked_users(self):
        """Returns the unique users from the linked users dictionary"""

        if len(self.linked_users) > 0:

            col_1 = set(self.linked_users["User 1"])
            col_2 = set(self.linked_users["User 2"])
            combined = col_1.union(col_2)

            return len(combined)
        else:
            return 0



    ## Collect round information from the evaluation id
    def get_evaluation_rounds(self):
        """Collect the timing and limits for the rounds from the evaluation under investigation"""

        ## evaluation information
        url = f"/evaluation/{self.evaluation}/round/list"
        EvaluationRoundListRequest = json.dumps({"nextPageToken": None})

        ## Collection evaluation
        round_list = self.syn.restPOST(url, body=EvaluationRoundListRequest)["page"]

        ## Gather round information
        rounds = []
        for round in round_list:
            temp = {}
            temp["roundStart"] = round["roundStart"]
            temp["roundEnd"]   = round["roundEnd"]
            temp["limit"]      = round["limits"][0]["maximumSubmissions"]
            rounds.append(temp)
        
        rounds = pd.DataFrame(rounds)
        rounds["roundStart"] = pd.to_datetime(rounds["roundStart"])
        rounds["roundEnd"] = pd.to_datetime(rounds["roundEnd"])

        return rounds

        
        

    ## create a link between two users
    def link_users(self, users: tuple, reason: str, abbr_reason: str, score: float):
        """
        Creates a new link between two users and associates a numerical score to the link and a reason for the link.
        Adds the new link to the linked_users dictionary in the CheatDetection object.  

        Args:
            users (tuple): A tuple of two users who should be linked. The 
            reason (str): Description of the reason for linking the two users
            abbr_reason (str): Short title for the type of reason linking the two users.
            score (float): Numerical float value associated with the measure. The 
                magnitude of the score will depend on what it is measuring

        Returns:
            N/A, nothing is returned from this function. The linked_users dictionary is updated directly.
        """
        users = sorted(users)
        
        temp_df = pd.DataFrame([[users[0], users[1], reason, abbr_reason, score]], columns=["User 1", "User 2", "Reasons", "Abbr Reason", "Scores"])

        self.linked_users = pd.concat([self.linked_users, temp_df])



    ## 1. Collect submissions from the evaluation queue
    ## 2. Identify users who may be in cahoots by sharing files
    def collect_submissions(self):
        """
        Collects all the ACCEPTED submissions in the evaluation queue under investigation and pulls all the relevant information from each submission
        and puts it into the accepted_submissions pandas dataframe.
        In addition, for each submission, if the users who created, modified, or submitted the file that was submitted to the queue are different,
        the two users are linked in the linked_users dictionary.

        Returns:
            N/A, nothing is returned from this function. The accepted_submissions dictionary and the linked_users object is updated directly.
        """
        for submission in self.syn.getSubmissions(self.evaluation, status='ACCEPTED'):

            ## submission user information
            submitting_user = submission["userId"]
            submitting_username = self.syn.getUserProfile(submitting_user)['userName']

            ## submission information bundle
            submission_information = json.loads(submission['entityBundleJSON'])
            
            ## Entity type of the submission
            entityType = submission_information["entityType"]

            ## If entity if file type
            if entityType == "file":

                ## collect file entity information
                file = submission_information['entity']

                ## collect user and filename information for further evaluation
                fileName = file["name"]
                current_submission = {
                    "user": submitting_user,
                    "username": submitting_username,
                    "createdOn": submission["createdOn"].split("T")[0],
                    "filename": fileName,
                    "count": 1
                }
                self.accepted_submissions.append(current_submission)

                user_created = file["createdBy"]
                user_modified = file["modifiedBy"]

                ## when the submitting user is not the same user that created or last modified the file
                ## link the two different users as collaborators
                if submitting_user != user_created or submitting_user != user_modified:
                    
                    ## collect users who created and modified the submitted file
                    file_creation_users = self.syn.getUserProfile(user_created)['userName']
                    file_modified_users = self.syn.getUserProfile(user_modified)['userName']
                    
                    ## Link differentiating users
                    if submitting_user != user_created:
                        users = tuple([submitting_username, file_creation_users])

                        self.link_users(users, "file creator and submitter are different", "Different Users", 1.0)


                    if submitting_user != user_modified:
                        users = tuple([submitting_username, file_modified_users])

                        self.link_users(users, "file modifier and submitter are different", "Different Users", 1.0)
                    

                    if user_created != user_modified:
                        users = tuple([user_created, file_modified_users])

                        self.link_users(users, "file creator and file modifier are different", "Different Users", 1.0)
    


    def filename_similarity(self):
        """
        Calculates the Jaro distance between the names of each submitted filename for each of the user pairs in the accepted submissions.
        Each user pair is found by looking at all the different users who submitted something on the same day.
        Function acts on the linked_users object
        """

        submitted_files = pd.DataFrame(self.accepted_submissions)[["username", "createdOn", "filename"]].drop_duplicates()
        submitted_files = submitted_files.merge(submitted_files, how="inner", on="createdOn")
        submitted_files = submitted_files[submitted_files["username_x"] != submitted_files["username_y"]]

        ## Calculate Jaro Distance between each of the filenames
        ## Jaro distance is a string-edit distance that gives a floating point response in [0,1] where 0 
        ## represents two completely dissimilar strings and 1 represents identical strings.
        submitted_files['similarity'] = submitted_files.apply(lambda row: j.jaro_similarity(row["filename_x"], row["filename_y"]), axis=1)

        ## Filter out similarities below 0.7
        submitted_files = submitted_files[submitted_files['similarity'] > 0.7]

        ## Add user linkes to linked user dictionary
        submitted_files.apply(lambda row: self.link_users(users=tuple([row["username_x"], row["username_y"]]), reason=f"Filename similarity: {row['filename_x']}, {row['filename_y']}", abbr_reason="Filename Similarity", score=row["similarity"]  ) , axis=1)



    def user_submission_pairwise_comparison(self):
        """
        Calculates the number of times two users submit to the challenge on the same and filters out the combined counts that fall under the submission limit.
        """
        
        ## Collecte all valid submissions from the evaluation queue
        number_of_accepted_submissions = pd.DataFrame(self.accepted_submissions)

        ## Calculate the number of submissions per user per day
        number_of_accepted_submissions = pd.DataFrame(number_of_accepted_submissions.groupby(["username", "createdOn"])["count"].sum()).reset_index()

        ## Find all pairs of users who submitted on the same day
        combined_accepted_submissions = number_of_accepted_submissions.merge(number_of_accepted_submissions, on="createdOn")
        
        ## Create unique username pair key
        combined_accepted_submissions["usernames"] = combined_accepted_submissions.apply(lambda row: tuple(sorted([row["username_x"], row["username_y"]])), axis=1)
        
        ## Calculate the number of combined submissions the user pair submitted in a single day
        combined_accepted_submissions["combined_counts"] = combined_accepted_submissions["count_x"] + combined_accepted_submissions["count_y"]

        ## Filter out rows where the usernames are the same
        combined_accepted_submissions = combined_accepted_submissions[combined_accepted_submissions["username_x"]!=combined_accepted_submissions["username_y"]]

        ## Identify round submission limits
        ## Currently only can handle DAILY submission limit
        ## TODO: Add handlers for MONTHLY submission limits
        evaluation_rounds = self.get_evaluation_rounds()
        combined_accepted_submissions = combined_accepted_submissions.merge(evaluation_rounds, how="cross")
        combined_accepted_submissions = combined_accepted_submissions[(combined_accepted_submissions["createdOn"]>=combined_accepted_submissions["roundStart"]) & (combined_accepted_submissions["createdOn"]<=combined_accepted_submissions["roundEnd"])]

        ## Filter out pairs where the combined submissions are not more than the daily limit
        combined_accepted_submissions = combined_accepted_submissions[combined_accepted_submissions["combined_counts"] > combined_accepted_submissions["limit"]]
        combined_accepted_submissions["combined_counts"] = 1

        ## Sum together the co-occurrence pairs
        combined_accepted_submissions = pd.DataFrame(combined_accepted_submissions.groupby("usernames")["combined_counts"].sum()).reset_index()
        
        ## Add all pairs as possible linked users
        combined_accepted_submissions.apply(lambda row: self.link_users(users=row["usernames"], reason=f"Submission Co-occurrence", abbr_reason="Submission Co-occurrence", score=row["combined_counts"] ), axis=1 )

        ## Filter out co-occurrences that don't have accompanying suspicious activity
        self.filter_cooccurrences()
    


    def filter_cooccurrences(self):
        """
        User pairs that are only linked due to submission co-occcurrence and no other reason are removed from the suspect list.
        Function acts on the linked_users object
        """
        
        ## Select pairs that are linked by co-occurrence
        cooccurrance_reasons = self.linked_users[self.linked_users["Reasons"]=="Submission Co-occurrence"]

        ## Select pairs that are linked for other reasons
        other_reasons = self.linked_users[self.linked_users["Reasons"]!="Submission Co-occurrence"]

        ## Find user pairs that are linked by co-occurrence and another reason
        df = other_reasons.merge(cooccurrance_reasons, on=["User 1", "User 2"], how="inner")[["User 1", "User 2"]].drop_duplicates()

        ## Filter user pairs to combined co-occurrence and other reasons
        self.linked_users = self.linked_users.merge(df, on=["User 1", "User 2"], how="inner")



    def collect_user_interaction_summary(self):
        """
        Collect interaction reports from the previously run tests
        """

        ## Collect users that submitted or modified the same model
        diff_users = self.linked_users[self.linked_users["Abbr Reason"]=="Different Users"].pivot_table(index=["User 1", "User 2"], columns="Abbr Reason", values="Scores", aggfunc=sum).reset_index()

        ## Collect users that both submitted similarly named files
        file_sim = self.linked_users[self.linked_users["Abbr Reason"]=="Filename Similarity"].pivot_table(index=["User 1", "User 2"], columns="Abbr Reason", values="Scores", aggfunc=max).reset_index()
        
        ## Collect users that both submitted on the same day for more than than the daily limit
        sub_coocc = self.linked_users[self.linked_users["Abbr Reason"]=="Submission Co-occurrence"].pivot_table(index=["User 1", "User 2"], columns="Abbr Reason", values="Scores", aggfunc=sum).reset_index()
        
        ## Merge the different user pairs
        report = self.linked_users[["User 1", "User 2"]].merge(diff_users, on=["User 1", "User 2"], how="left")
        report = report.merge(file_sim, on=["User 1", "User 2"], how="left")
        report = report.merge(sub_coocc, on=["User 1", "User 2"], how="left").fillna(0.0).drop_duplicates()

        ## Calculate score totals
        report["Score Totals"] = report.apply(lambda row: row["Different Users"] + row["Filename Similarity"] + row["Submission Co-occurrence"], axis=1)

        return report


    def user_cluster_detection(self, max_iterations=30):

        ## TODO: There are more efficient and less open ended algorithms for identify open and closed clusters in networks. One of them should be implemented here.

        """
        Identifies possible clusters of users that could be coordinating to skirt the daily submission limit.

        Args:
            max_iterations (int): The number of times the function should try to iterively build clusters

        Returns:
            N/A, nothing is returned from this function. The user_clusters dictionary is updated directly.
        """
        
        ## collect user interation summary table
        users = self.collect_user_interaction_summary()
        
        ## collect all unique users in the 
        unique_users = set(users["User 1"]).union(set(users["User 2"]))

        clusters = {u: [u] for u in unique_users}

        old_clusters = {}
        count = 1
        
        ## iteratively build possible clusters
        while old_clusters != clusters:

            old_clusters = copy.deepcopy(clusters)

            for index,row in users.iterrows():
                
                user_1 = row["User 1"]
                user_2 = row["User 2"]
                #score = row["Score Totals"]

                clusters[user_1].append(user_2)
                clusters[user_2].append(user_1)

                if user_2 in clusters[user_1]:
                    clusters[user_1] += clusters[user_2]
                
                if user_1 in clusters[user_2]:
                    clusters[user_2] += clusters[user_1]

                clusters[user_1] = sorted(list(set(clusters[user_1])))
                clusters[user_2] = sorted(list(set(clusters[user_2])))

            count += 1
            if count > max_iterations:
                print (f"User cluster identification incomplete after {max_iterations} iterations")
                break

        
        ## build cluster reports and add clusters to user_clusters
        group = 1
        visit_clusters = []

        for cluster in clusters.values():
            if cluster not in visit_clusters:
                
                ## Calculate the average user pair scores for the cluster
                score_temp = pd.DataFrame({
                    "Group": f"Group {group}",
                    "Users": cluster
                })
                average_score = np.mean(score_temp.merge(users, left_on="Users", right_on="User 1", how="inner")["Score Totals"])

                ## Put each cluster's information into a pandas row
                temp = pd.DataFrame([{
                    "Group": f"Group {group}",
                    "Clusters": ", ".join(cluster),
                    "Average Score": average_score
                }])

                self.user_clusters = pd.concat([self.user_clusters, temp])

                ## track the visited clusters
                visit_clusters.append(cluster)
                
                group += 1

        ## Set group as index and order by the average score
        self.user_clusters = self.user_clusters.set_index("Group").sort_values("Average Score", ascending=False)



    ## Build and print report
    def report(self):
        """
        Generates a report from the linked_users object and prints out the report along with an explanation for interpreting the report.
        """
        report = self.collect_user_interaction_summary()

        report = report.sort_values("Score Totals", ascending=False)
        print ("\n\n")
        print ("============================================= REPORT SUMMARY =============================================")
        print ("\t\tThese are the username pairs that have raised flags for potentially being either")
        print ("\t\tfrom the same user or the same team to skirt the submission limits. User pairs in")
        print ("\t\tthe report have at least one day of submission co-occurrences where the total")
        print ("\t\tsubmissions are greater than the daily limit and they have at least one other")
        print ("\t\tlinking activity.")

        print ("Different Users: \t\tCounts the number of times the two users created, submitted, or modified the same file.")
        print ("Filename Similarity: \t\tShows the maximum Jaro similarity of possible shared submitted files.")
        print ("Submission Co-occurrence: \tCounts the number of times the two users submitted on the same day more than 2 submissions combined.")
        print (tabulate(report, headers='keys', tablefmt='psql', showindex=False))

        print ("\n")
        print ("---------------------------------------- CLUSTER ANALYSIS ----------------------------------------")
        print (tabulate(self.user_clusters, headers="keys", tablefmt="fancy_grid"))



    ## Run the cheat detection functions
    def cheat_detection(self):
        """
        Run all the different cheat detection tests and print out the user pairs and cluster reports.
        """

        print ("Finding users in cahoots...")
        self.collect_submissions()

        print ("Calculating filename similarities...")
        self.filename_similarity()

        print ("Calculating submission cooccurrences...")
        self.user_submission_pairwise_comparison()

        print ("Identifying user clusters...")
        self.user_cluster_detection()

        ## ADD NEW TESTS HERE
        ## New tests that are created should be run prior to the report

        print ("Generating report...")
        self.report()



if __name__ == "__main__":

    syn = Synapse()
    syn.login()

    QUEUE = 9614925

    cd = CheatDetection(syn=syn, evaluation_id=QUEUE)

    
    cd.cheat_detection()
