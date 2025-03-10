from collections.abc import Sequence
import re
import functools

from concordia.document import interactive_document
from concordia.language_model import language_model
from concordia.typing import clock as game_clock
from concordia.typing import entity as entity_lib
from concordia.typing import entity_component
from concordia.typing import logging
from concordia.utils import concurrency, helper_functions
from typing_extensions import override
DEFAULT_PRE_ACT_KEY = 'Act'
from collections.abc import Mapping
from concordia.components import agent as agent_components
def _get_class_name(object_: object) -> str:
  return object_.__class__.__name__

class MCTSActComponent(entity_component.ActingComponent):
    def __init__(
            self,
            model: language_model.LanguageModel,
            clock: game_clock.GameClock,
            num_proposed_actions: int,
            desire_component_dict: Mapping[str, entity_component.ContextComponent], # component class name: component instance
            component_order: Sequence[str] | None = None,
            pre_act_key: str = DEFAULT_PRE_ACT_KEY,
            logging_channel: logging.LoggingChannel = logging.NoOpLoggingChannel,
    ):

      self._model = model
      self._clock = clock
      if component_order is None:
          self._component_order = None
      else:
          self._component_order = tuple(component_order)
      if self._component_order is not None:
          if len(set(self._component_order)) != len(self._component_order):
              raise ValueError(
                  'The component order contains duplicate components: '
                  + ', '.join(self._component_order)
              )

      self._pre_act_key = pre_act_key
      self._logging_channel = logging_channel
      self._num_proposed_actions = num_proposed_actions
      self._desire_component_dict = desire_component_dict
      self._desire_component_names = tuple(_get_class_name(compo) for compo in self._desire_component_dict.values())
      self._desire_name = tuple(self._desire_component_dict.keys())

    def _get_desire_status(self):
        desire_status = ''
        agent_name = self.get_entity().name
        for name, compo in self._desire_component_dict.items():
          desire_status += f"{agent_name}'s {name}: {compo.get_pre_act_value()}\n"
        return desire_status

    def _get_desire_name(self):
        return self._desire_name

    def _context_for_action(
        self,
        contexts: entity_component.ComponentContextMapping,
    ) -> str:
        if self._component_order is None:
            return '\n'.join(
                context for context in contexts.values() if context
        )

        desire_set = set(self._desire_component_names)
        filtered_component_order = tuple(item for item in self._component_order if item not in desire_set)
        filtered_context_keys = tuple(sorted(set(contexts.keys()) - set(self._component_order) - desire_set))

        order = filtered_component_order + filtered_context_keys + self._desire_component_names

        desire_context = '\n'.join(contexts[name] for name in order if contexts[name])
        return desire_context

    def _preprocess_imagined_action(self, imagined_actions: str) -> list:
        action_sequences = []
        for i in range(self._num_proposed_actions):
          if f"Activity {i+1}: " not in imagined_actions:
            break
          action = imagined_actions.split(f"Activity {i+1}: ")[1].split("\n")[0]

          action_sequences.append(action)
        return action_sequences

    def _imagine_result_of_action(self, proposed_action):
        prompt = interactive_document.InteractiveDocument(self._model)
        # imagine_prompt = ('You are a human-like agent, '
        #                  'you will receive a series of observations describe your desire in many dimensions '
        #                  'and an action you take in current time step. '
        #                  'You need to first analyse how your desires change after the action you take, '
        #                  'and then output the states of desire-state observations in the same format as your input.\n')
        # action_context = f'You take the action: {proposed_action} \n'
        agent_name = self.get_entity().name
        imagine_prompt = (f'{agent_name} is a human-like agent, '
                          f'{agent_name} will receive a series of observations describing desires in many dimensions '
                          'and an action taken in the current time step. '
                          f'{agent_name} needs to first analyze how desires change after the action taken, '
                          'and then output the states of desire-state observations in the same format as the input.\n')

        action_context = f'{agent_name} takes the action: \n{proposed_action} \n'
        desire_status = f"{agent_name}'s original desire states: \n{self._get_desire_status()}\n"
        output_format = (f"Please output the states of desire-state observations in the following format: \n")
        for desire in self._desire_name:
            output_format += f"{desire}: <{desire} state> \n"
        total_prompt = imagine_prompt + desire_status + action_context + output_format
        imagined_states = prompt.open_question(
            total_prompt,
            max_tokens=2200,
            terminators=(),
            question_label='Exercise',
        )
        return {"status": imagined_states, "prompt": prompt.view().text()}
    @override
    def get_action_attempt(
        self,
        contexts: entity_component.ComponentContextMapping,
        action_spec: entity_lib.ActionSpec,
    ) -> str:
        prompt = interactive_document.InteractiveDocument(self._model)
        context = self._context_for_action(contexts)
        prompt.statement(context + '\n')
        agent_name = self.get_entity().name

        MCTS_log = dict()
        MCTS_log['component context'] = context

        tree_thinking_prompt = (f"{agent_name} is the human-like desire-driven agent, "
                        f"{agent_name} will observe current states over "
                        f"{', '.join(self._desire_name)} "
                        f"which represent {len(self._desire_name)} desire or value dimensions. "
                        "Given these state descriptions, "
                        f"please generate {self._num_proposed_actions} activities "
                        "(which may contain several feasible actions for each) "
                        f"that might have the most positive impact on {agent_name}'s desires (including physical and mental)."
                        f"{agent_name} needs to focus on immediate desires and take activities that can satisfy them, "
                        f"but at the same time, {agent_name} must ensure that actions are reasonable and varied. "
                        f"Notice that {agent_name} can only interact with items provided by the environment. "
                        f"{agent_name} needs to describe activities in a more specific mode and ensure "
                        "that the time required for the action sequence matches the required time period. "
                        f"Please output the {self._num_proposed_actions} activities in the following format:\n"
                        "'Activity 1: <first possible action sequence> \n"
                        "Activity 2: <second possible action sequence> \n"
                        "Activity 3: <third possible action sequence> \n ......' "
                        "and ensure that the time required for the action sequence matches the required time period.")
        call_to_action = action_spec.call_to_action.format(
            name=self.get_entity().name,
            timedelta=helper_functions.timedelta_to_readable_str(
                self._clock.get_step_size()
            ),
        )

        tree_thinking_prompt = tree_thinking_prompt + '\n' + call_to_action

        tree_thinking_answer = prompt.open_question(
            tree_thinking_prompt,
            max_tokens=1200,
            terminators=(),
            question_label='Exercise',
        )
        MCTS_log['tree_thinking_prompt'] = prompt.view().text()
        MCTS_log['tree_thinking_answer'] = tree_thinking_answer
        imagined_actions = self._preprocess_imagined_action(tree_thinking_answer)
        MCTS_log['imagined_actions'] = imagined_actions

        result_of_imagined_actions = concurrency.run_tasks({
          query: functools.partial(self._imagine_result_of_action, query)
          for query in imagined_actions
        })

        MCTS_log['result_of_imagined_actions'] = result_of_imagined_actions
        result_of_imagined_actions = {key: value['status'] for key, value in result_of_imagined_actions.items()}

        prompt = interactive_document.InteractiveDocument(self._model)

        desire_status = self._get_desire_status()
        observation_status = self.get_entity().get_component("Observation", type_=agent_components.action_spec_ignored.ActionSpecIgnored).get_pre_act_value()
        action_selection_prompt = (
                           f"{agent_name} is a human-like agent. "
                           f"{agent_name} will first receive a series of observations "
                           "describing the current states of desires in many dimensions. "
                           f"Then, {agent_name} will receive several feasible actions along with the states of desire "
                           "after taking each action. "
                           f"{agent_name} needs to compare these actions and their corresponding states of desire, "
                           f"and choose the action that has the most positive impact on all desires of {agent_name} "
                           f"or value states. {agent_name} should focus on immediate desires "
                           "and take actions that can satisfy them. "
                           )
        action_selection_prompt += (
                            f"The observations of the surrounding environment: \n"
                            f"{observation_status} \n"
                            f"Alice's current states of desire: \n"
                            f"{desire_status} \n"
        )
        action_and_result = f"Following are the states of desire after each action: \n"
        for i in range(self._num_proposed_actions):
          if i >= len(imagined_actions):
            break
          action = imagined_actions[i]
          action_and_result += f'Action {i+1}: {action} \n'
          action_and_result += f'States after action {i+1}: {result_of_imagined_actions[action]} \n\n'

        action_selection_prompt += action_and_result

        action_selection_prompt += (f'Please output the specific best action instead without explanation of <Action 1> or <Action 2> and so on. '
                                    'If there is only one action provided, output the action content directly. \n')
        action_selection_prompt += (f"Please output the best action in the following format: \n"
                                    f"'Action: <{agent_name}'s best action>' \n"
                                    f"Example: Action: {agent_name} observes the surroundings.\n")

        o = prompt.open_question(action_selection_prompt, max_tokens=2200,terminators=())

        if o.startswith('Action'):
            o = o.split('Action', 1)[1].strip(' :')
        output = o
        MCTS_log['action_selection_prompt'] = prompt.view().text()
        MCTS_log['action_selection_answer'] = output
        self._log(MCTS_log, prompt)
        return output

    def _log(self,
           result: str,
           prompt: interactive_document.InteractiveDocument):
        self._logging_channel({
            'Key': self._pre_act_key,
            'Value': result,
            'Prompt': prompt.view().text().splitlines(),
        })

    def get_state(self) -> entity_component.ComponentState:
        """Converts the component to a dictionary."""
        return {}

    def set_state(self, state: entity_component.ComponentState) -> None:
      pass
