# D2A
**\[ICLR 2025\] Simulating Human-like Daily Activities with Desire-driven Autonomy**

paper link: [http://arxiv.org/abs/2412.06435](http://arxiv.org/abs/2412.06435)

![GIF](imgs/video_v3.gif)
## Abstract

Existing task-oriented AI agents often depend on explicit instructions or external rewards, limiting their ability to be driven by intrinsic motivations like humans. In this paper, we present a desire-driven autonomy framework to guide a Large Language Model based(LLM-based) agent to simulate human-like daily activities. In contrast to previous agents, our Desire-driven Autonomous Agent (D2A) operates on the principle of intrinsic desire, allowing it to propose and select tasks that fulfill its motivational framework autonomously. Inspired by the Theory of Needs, the motivational framework incorporates an understanding of human-like desires, such as the need for social interaction, personal fulfillment, and self-care. Utilizing a desire-driven task generation mechanism, the agent evaluates its current state and takes a sequence of activities aligned with its intrinsic motivations. Through simulations, we demonstrate that our Desire-driven Autonomous Agent (D2A) generates coherent, contextually relevant daily activities while exhibiting variability and adaptability similar to human behavior. A comparative analysis with other LLM-based frameworks demonstrates that our approach significantly enhances the rationality of the simulated activities

## Desire-driven Autonomous Agent Framework

![image](imgs/framework.png)

## Environment
1. Clone D2A:
```bash
git clone https://github.com/zfw1226/D2A
cd D2A
```
2. Install the D2A module
```bash
conda env create -f environment_D2A.yml
conda activate D2A
```
3. Re-install the Concordia module (in the `D2A` folder that contains `concordia` and `examples`)
```bash
pip install -e .[dev]
```


## Usage

The D2A environment is under the `examples/D2A` folder.

In D2A folder the file structure is:
```
examples/
├── D2A/
│   ├── Baseline_agent/
│   │   ├── BabyAGI_ActComp.py
│   │   ├── Baseline_BabyAGI.py
│   │   ├── Baseline_comp.py
│   │   ├── Baseline_LLMob.py
│   │   ├── Baseline_ReAct.py
│   │   ├── LLMob_ActComp.py
│   │   └── ReAct_ActComp.py
│   └── D2A_agent/
│       ├── Value_ActComp.py
│       └── ValueAgent.py
├── Environment_construction/
│   └── generate_indoor_situation.py
├── NPC_agent/
│   └── generic_support_agent.py
├── result_folder/
├── value_components/
│   ├── hardcoded_value_state.py
│   └── init_value_info_social.py
│
├── value_comp.py
├── __init__.py
├── experiment_setup_indoor.py
├── experiment_setup_outdoor.py
├── indoor_Room.py
├── NullObservation.py
└── outdoor_party.py
```

## Usage


### Run the simulation
1. Set up the **environment dependencies** by following **Environment** section

2. Set up the **experiment setting** in `experiment_setup_indoor.py` and `experiment_setup_outdoor.py`
   - ROOT (the root path of the project, the folder which has `concordia` and `examples` in it)
   - episode_length
   - disable_language_model
   - st_model
   - tested_agents
   - whether to use previous profile
     - Use_Previous_profile
     - previous_profile_file
     - previous_profile
     - previous_profile's path
   - Backbone LLM (details refers to concordia package)
     - api_type
     - model_name
     - api_key
   - desires-related stuff (the desire dimensions to be used while simulating)
     - visible_desires (will appear in the context as the hint for the agent)
     - hidden_desires (will not appear in the context as the hint for the agent)
   - the path to store the result

3. **run the simulation** by `python PATH/to/indoor_Room.py` or `python PATH/to/outdoor_party.py`

## To modify desire-related components, navigate to the `value_components` folder and follow these steps across different files:
_assume that we want to add a new desire called `sense of wonder`_
### value_comp.py
1. create the new desire component subclass in `value_comp.py`
  ```python
  # example:
  class SenseOfWonderWithoutPreAct(desireWithoutPreAct):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
  class SenseOfWonder(desire):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
  ```
### init_value_info_social.py
1. Modify the profile_dict by adding a new entry:
  ```python
    # {"descriptive_adjective": "desire_name"}
    # example:
    profile_dict = {
      'gluttonous': 'hunger',
      # ...
      "curious": "sense of wonder",
    }
  ```
2. Add the desire name to the `values_names` list
  ```python
    values_names = [
      'hunger',
      # ...
      "sense of wonder",
  ]
  ```
3. Add corresponding descriptions to `values_names_descriptions`
  ```python
  values_names_descriptions = {
    'hunger': 'The value....',
    # ....
    'sense of wonder': "The value of sense of wonder ranges from 0 to 10. A score of 0 means you feel no curiosity or amazement about the world, lacking any interest in exploration or new experiences, while a score of 10 means you are deeply fascinated and captivated by the world around you, constantly seeking to discover, learn, and marvel at new things."
  }
  ```
4. Add corresponding subclass to `get_all_desire_components` and `get_all_desire_components_without_PreAct`.
  ```python
  def get_all_desire_components_without_PreAct():
    for desire in wanted_desires:
      if desire == 'hunger':
        init = value_comp.HungerWithoutPreAct
      # ......
      elif desire == 'sense of wonder':
        init = value_comp.SenseOfWonderWithoutPreAct
      # ......

  def get_all_desire_components():
    for desire in wanted_desires:
      if desire == 'hunger':
        init = value_comp.Hunger
      # ......
      elif desire == 'sense of wonder':
        init = value_comp.SenseOfWonder
      # ......
  ```
### hardcoded_value_state.py
1. Add numerical value mappings to `hardcore_state`. You can use GPT to design appropriate mapping scales.
  ```python
  hardcode_state = {
    'hunger': {'...': '.....'},
    # ......
    'sense of wonder': {
      0: "No curiosity or amazement about the world, lacking any interest in exploration or new experiences.",
      1: "Very low sense of wonder, rarely feeling curious or amazed by anything.",
      2: "Minimal sense of wonder, occasionally feeling a slight curiosity about the world.",
      3: "Somewhat low sense of wonder, infrequently feeling a mild interest in new experiences.",
      4: "Slight sense of wonder, occasionally feeling curious or amazed by certain things.",
      5: "Moderate sense of wonder, sometimes feeling curious and interested in exploring new things.",
      6: "Noticeable sense of wonder, often feeling curious and amazed by many aspects of the world.",
      7: "Strong sense of wonder, frequently feeling a deep fascination and desire to explore and understand the world.",
      8: "Very strong sense of wonder, consistently feeling captivated and eager to discover new things.",
      9: "Extremely strong sense of wonder, feeling intensely curious and amazed by almost everything around you.",
      10: "Complete sense of wonder, deeply fascinated and constantly seeking to discover, learn, and marvel at new things."
    }
  }
  ```
  The prompt can be like:
  ```python
  prompt = (
    "describe 'sense of wonder' in the format of the example, sense of wonder is defined as: The value of sense of wonder ranges from 0 to 10. A score of 0 means you feel no curiosity or amazement about the world, lacking any interest in exploration or new experiences, while a score of 10 means you are deeply fascinated and captivated by the world around you, constantly seeking to discover, learn, and marvel at new things.\n"
    "Example: \n"
    """
    'social connectivity': {
        0: "Completely isolated, lacking any meaningful social connections.",
        1: "Very lonely, minimal social connectivity and rare interactions.",
        2: "Disconnected, limited social interactions and frequent feelings of isolation.",
        3: "Somewhat isolated, occasional social engagements but still feeling disconnected.",
        4: "Slightly connected, some social interactions but not very strong or supportive.",
        5: "Moderately connected, a few meaningful relationships and occasional social interactions.",
        6: "Regularly engaged, growing network of social connections.",
        7: "Socially connected, several meaningful and supportive relationships.",
        8: "Highly connected, strong network of friends and supportive relationships.",
        9: "Profoundly connected, deep and meaningful social relationships.",
        10: "Highly socially connected, strong and supportive network of relationships."
      }
      """
    )
  ```

### experiment_setup_outdoor.py or experiment_setup_indoor.py
1. Add desire name to `wanted_desires` and `hidden_desires(optional)`
  ```python
  wanted_desires = [
  'hunger',
  # ......
  'sense of wonder'
  ]
  ```

#### Optional: Enable LLM Value Conversion
To use LLM for action value conversion, reach `value_comp.py`
- replace `_convert_numeric_desire_to_qualitative_by_hard_coding(self)` function in the `_make_pre_act_value(self)` with `_convert_numeric_desire_to_qualitative(self)`.

## Citation D2A
If you use D2A in your work, please cite the article:
```bibtex
@inproceedings{
wang2025simulating,
title={Simulating Human-like Daily Activities with Desire-driven Autonomy},
author={Yiding Wang and Yuxuan Chen and Fangwei Zhong and Long Ma and Yizhou Wang},
booktitle={The Thirteenth International Conference on Learning Representations},
year={2025},
url={https://openreview.net/forum?id=3ms8EQY7f8}
}
```
