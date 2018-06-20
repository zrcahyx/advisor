import json
import random

from suggestion.models import Study
from suggestion.models import Trial
from suggestion.algorithm.base_algorithm import BaseSuggestionAlgorithm


class GridSearchAlgorithm(BaseSuggestionAlgorithm):

    def get_new_suggestions(self, study_id, trials, number=1):
        """
    Get the new suggested trials with grid search.
    """
        study = Study.objects.get(id=study_id)

        result = []
        for i in range(number):
            trial = Trial.create(study.id, "GridSearchTrial")
            parameter_values_json = {}

            # TODO: Support different type of parameters

            study_configuration_json = json.loads(study.study_configuration)
            params = study_configuration_json["params"]
            for param in params:
                min_value = param["minValue"]
                max_value = param["maxValue"]

                if number > 1:
                    value_step = (max_value - min_value) / (number - 1)
                else:
                    value_step = max_value - min_value
                parameter_value = min_value + value_step * i
                parameter_values_json[param["parameterName"]] = parameter_value

            trial.parameter_values = json.dumps(parameter_values_json)
            trial.save()
            result.append(trial)

        return result
