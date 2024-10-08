import pandas as pd
import numpy as np
import json
import pathlib
import re
import matplotlib.pyplot as plt
from typing import Union, Tuple

class QuestionnaireAnalysis:
    """
    Reads and analyzes data generated by the questionnaire experiment.
    Should be able to accept strings and pathlib.Path objects.
    """

    def __init__(self, data_fname: Union[pathlib.Path, str]):
        self.data_fname = data_fname
        self.data = None

    def read_data(self):
        """Reads the json data located in self.data_fname into memory, to the attribute self.data."""
        with open(self.data_fname, 'r') as file:
            self.data = pd.DataFrame(json.load(file))



    def show_age_distrib(self) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates and plots the age distribution of the participants."""
        # Convert the 'age' column to numeric, forcing errors to NaN
        self.data['age'] = pd.to_numeric(self.data['age'], errors='coerce')
        
        # Drop NaN values from ages
        ages = self.data['age'].dropna()
        
        # Define bins for the histogram
        bins = np.arange(0, 101, 10)
        
        # Calculate the histogram
        hist, bins = np.histogram(ages, bins=bins)
        
        # Plot the histogram
        plt.hist(ages, bins=bins, edgecolor='black')
        plt.xlabel('Age')
        plt.ylabel('Number of Participants')
        plt.title('Age Distribution of Participants')
        plt.show()
        
        return hist, bins

    def remove_rows_without_mail(self) -> pd.DataFrame:
        """Checks self.data for rows with invalid emails, and removes them."""
        def is_valid_email(email):
            if isinstance(email, str):
                # Basic email validation conditions
                if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    return True
            return False

        valid_email_mask = self.data['email'].apply(is_valid_email)
        cleaned_data = self.data[valid_email_mask].reset_index(drop=True)
        return cleaned_data


    def fill_na_with_mean(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """Finds, in the original DataFrame, the subjects that didn't answer all questions, and replaces that missing value with the mean of the other grades for that student."""
        data_filled = self.data.copy()
        row_indices = []

        for idx, row in data_filled.iterrows():
            if row.isnull().any():
                row_indices.append(idx)
                for col in ['q1', 'q2', 'q3', 'q4', 'q5']:
                    if pd.isna(row[col]):
                        mean_value = row[['q1', 'q2', 'q3', 'q4', 'q5']].mean(skipna=True)
                        data_filled.at[idx, col] = mean_value

        return data_filled, np.array(row_indices)


    def score_subjects(self, maximal_nans_per_sub: int = 1) -> pd.DataFrame:
        """Calculates the average score of a subject and adds a new "score" column with it."""
        
        # Ensure the columns are numeric, converting errors to NaN
        for col in ['q1', 'q2', 'q3', 'q4', 'q5']:
            self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
        
        def calculate_score(row):
            if row.isnull().sum() > maximal_nans_per_sub:
                return pd.NA
            else:
                return int(np.floor(row.mean(skipna=True)))

        scores = self.data[['q1', 'q2', 'q3', 'q4', 'q5']].apply(calculate_score, axis=1)
        self.data['score'] = scores.astype("UInt8")
        return self.data



    def correlate_gender_age(self) -> pd.DataFrame:
        """Looks for a correlation between the gender of the subject, their age and the score for all five questions."""
        
        # Ensure that the 'age' column is numeric
        self.data['age'] = pd.to_numeric(self.data['age'], errors='coerce')

        # Categorize age into groups above or below 40
        self.data['age_group'] = self.data['age'].apply(lambda age: 'above_40' if age >= 40 else 'below_40')
        
        # Group by gender and age group, then calculate the mean for only numeric columns
        grouped = self.data.groupby(['gender', 'age_group']).mean(numeric_only=True)
        
        # Return only the relevant question columns
        return grouped[['q1', 'q2', 'q3', 'q4', 'q5']]
    
    

if __name__ == '__main__':
    q = QuestionnaireAnalysis('data.json')
    q.read_data()
    q.show_age_distrib()
    q.remove_rows_without_mail()
    q.fill_na_with_mean()
    q.score_subjects()
    q.correlate_gender_age()