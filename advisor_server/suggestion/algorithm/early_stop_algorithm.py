import json
import random

from suggestion.models import Study
from suggestion.models import Trial
from suggestion.models import TrialMetric
from suggestion.algorithm.base_algorithm import BaseEarlyStopAlgorithm


class NoEarlyStopAlgorithm(BaseEarlyStopAlgorithm):

    def get_early_stop_trials(self, trials):
        return None


class EarlyStopFirstTrialAlgorithm(BaseEarlyStopAlgorithm):

    def get_early_stop_trials(self, trials):
        return trials[0]


class EarlyStopDescendingAlgorithm(BaseEarlyStopAlgorithm):

    def get_early_stop_trials(self, trials):
        result = []

        for trial in trials:
            study = Study.objects.get(id=trial.study_id)
            study_configuration_json = json.loads(study.study_configuration)
            study_goal = study_configuration_json["goal"]

            metrics = TrialMetric.objects.filter(
                trial_id=trial.id).order_by("-training_step")
            metrics = [metric for metric in metrics]

            if len(metrics) >= 2:
                if study_goal == "MAXIMIZE":
                    if metrics[0].objective_value < metrics[1].objective_value:
                        result.append(trial)
                elif study_goal == "MINIMIZE":
                    if metrics[0].objective_value > metrics[1].objective_value:
                        result.append(trial)

        return result
