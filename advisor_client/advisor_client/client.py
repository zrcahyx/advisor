import json
import logging
import requests

from .model import Study
from .model import Trial
from .model import TrialMetric


class AdvisorClient(object):

    def __init__(self, endpoint="http://0.0.0.0:8000"):
        self.endpoint = endpoint

    def create_study(self,
                     name,
                     study_configuration,
                     algorithm="BayesianOptimization"):
        url = "{}/suggestion/v1/studies".format(self.endpoint)
        request_data = {
            "name": name,
            "study_configuration": study_configuration,
            "algorithm": algorithm
        }
        response = requests.post(url, json=request_data)

        study = None
        if response.ok:
            study = Study.from_dict(response.json()["data"])

        return study

    def list_studies(self):
        url = "{}/suggestion/v1/studies".format(self.endpoint)
        response = requests.get(url)
        studies = []

        if response.ok:
            dicts = response.json()["data"]
            for dict in dicts:
                study = Study.from_dict(dict)
                studies.append(study)

        return studies

    # TODO: Support load study by configuration and name
    def get_study_by_id(self, study_id):
        url = "{}/suggestion/v1/studies/{}".format(self.endpoint, study_id)
        response = requests.get(url)
        study = None

        if response.ok:
            study = Study.from_dict(response.json()["data"])

        return study

    def get_suggestions(self,
                        study_id,
                        trials_number=1,
                        acq='ucb',
                        kappa=2.576,
                        xi=0.0):
        url = "{}/suggestion/v1/studies/{}/suggestions".format(
            self.endpoint, study_id)
        request_data = {
            "trials_number": trials_number,
            "acq": acq,
            "kappa": kappa,
            "xi": xi
        }
        response = requests.post(url, json=request_data)
        trials = []

        if response.ok:
            dicts = response.json()["data"]
            for dict in dicts:
                trial = Trial.from_dict(dict)
                trials.append(trial)

        return trials

    def is_study_done(self, study_id):
        study = self.get_study_by_id(study_id)
        is_completed = True

        if study.status == "Completed":
            return True

        trials = self.list_trials(study_id)
        for trial in trials:
            if trial.status != "Completed":
                return False

        url = "{}/suggestion/v1/studies/{}".format(self.endpoint,
                                                   trial.study_id)
        request_data = {"status": "Completed"}
        response = requests.put(url, json=request_data)

        return is_completed

    def list_trials(self, study_id):
        url = "{}/suggestion/v1/studies/{}/trials".format(
            self.endpoint, study_id)
        response = requests.get(url)
        trials = []

        if response.ok:
            dicts = response.json()["data"]
            for dict in dicts:
                trial = Trial.from_dict(dict)
                trials.append(trial)

        return trials

    def list_trial_metrics(self, study_id, trial_id):
        url = "{}/suggestion/v1/studies/{}/trials/{}/metrics".format(
            self.endpoint, study_id)
        response = requests.get(url)
        trial_metrics = []

        if response.ok:
            dicts = response.json()["data"]
            for dict in dicts:
                trial_metric = TrialMetric.from_dict(dict)
                trial_metrics.append(trial_metric)

        return trial_metrics

    def get_best_trial(self, study_id):
        if not self.is_study_done:
            return None

        study = self.get_study_by_id(study_id)
        study_configuration_dict = json.loads(study.study_configuration)
        study_goal = study_configuration_dict["goal"]
        trials = self.list_trials(study_id)
        # TODO: Check if the first trial has objective value
        best_trial = trials[0]

        for trial in trials:
            if study_goal == "MAXIMIZE":
                if trial.objective_value and trial.objective_value > best_trial.objective_value:
                    best_trial = trial
            elif study_goal == "MINIMIZE":
                if trial.objective_value and trial.objective_value < best_trial.objective_value:
                    best_trail = trial
            else:
                return None

        return best_trial

    def get_trial(self, study_id, trial_id):
        url = "{}/suggestion/v1/studies/{}/trials/{}".format(
            self.endpoint, study_id, trial_id)
        response = requests.get(url)
        trial = None

        if response.ok:
            trial = Trial.from_dict(response.json()["data"])

        return trial

    def create_trial_metric(self, study_id, trial_id, training_step,
                            objective_value):
        url = "{}/suggestion/v1/studies/{}/trials/{}/metrics".format(
            self.endpoint, study_id, trial_id)
        request_data = {
            "training_step": training_step,
            "objective_value": objective_value
        }
        response = requests.post(url, json=request_data)

        study = None
        if response.ok:
            trial_metric = TrialMetric.from_dict(response.json()["data"])

        return trial_metric

    def complete_trial_with_tensorboard_metrics(self, trial,
                                                tensorboard_metrics):
        for tensorboard_metric in tensorboard_metrics:
            self.create_trial_metric(trial.study_id, trial.id,
                                     tensorboard_metric.step,
                                     tensorboard_metric.value)

        url = "{}/suggestion/v1/studies/{}/trials/{}".format(
            self.endpoint, trial.study_id, trial.id)
        objective_value = tensorboard_metrics[-1].value
        request_data = {
            "status": "Completed",
            "objective_value": objective_value
        }

        response = requests.put(url, json=request_data)

        if response.ok:
            trial = Trial.from_dict(response.json()["data"])

        return trial

    def complete_trial_with_one_metric(self, trial, metric):
        self.create_trial_metric(trial.study_id, trial.id, None, metric)

        url = "{}/suggestion/v1/studies/{}/trials/{}".format(
            self.endpoint, trial.study_id, trial.id)
        objective_value = metric
        request_data = {
            "status": "Completed",
            "objective_value": objective_value
        }

        response = requests.put(url, json=request_data)

        if response.ok:
            trial = Trial.from_dict(response.json()["data"])

        return trial
