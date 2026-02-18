from typing import Callable

from loguru import logger

from tau2.data_model.message import AssistantMessage, Message, ToolCall, UserMessage
from tau2.data_model.simulation import DBCheck, EnvAssertionCheck, RewardInfo
from tau2.data_model.tasks import RewardType, Task
from tau2.environment.environment import Environment
from tau2.evaluator.evaluator_base import EvaluatorBase
from tau2.logfire_setup import is_logfire_enabled
from tau2.utils.utils import dict_diff_for_logging


class EnvironmentEvaluator(EvaluatorBase):
    """
    Evaluator focuses on endstate of the simulation environment.
    """

    @classmethod
    def calculate_reward(
        cls,
        environment_constructor: Callable[[], Environment],
        task: Task,
        full_trajectory: list[
            Message
        ],  # FIXME: It would be better to be able to get only the messages that are after the initial state
        solo_mode: bool = False,
    ) -> RewardInfo:
        """
        Calculate the reward for the simulation.
        Args:
            environment_constructor: Callable[[], Environment]
            task: Task
            full_trajectory: list[Message] (Must include the message history from task initial state)
            solo_mode: bool
        Returns:
            RewardInfo
        """
        if task.evaluation_criteria is None:
            return RewardInfo(
                reward=1.0,
                info={"note": "No evaluation criteria"},
            )
        expected_actions = task.evaluation_criteria.actions
        env_assertions = task.evaluation_criteria.env_assertions
        if expected_actions is None and env_assertions is None:
            return RewardInfo(
                reward=1.0,
                db_check=DBCheck(db_match=True, db_reward=1.0),
                info={"note": "No expected actions or env assertions"},
            )

        initialization_data = None
        if (
            task.initial_state is not None
            and task.initial_state.initialization_data is not None
        ):
            initialization_data = task.initial_state.initialization_data

        initialization_actions = None
        if (
            task.initial_state is not None
            and task.initial_state.initialization_actions is not None
        ):
            initialization_actions = task.initial_state.initialization_actions

        message_history = []
        if (
            task.initial_state is not None
            and task.initial_state.message_history is not None
        ):
            message_history = task.initial_state.message_history

        predicted_environment = environment_constructor(solo_mode=solo_mode)
        predicted_environment.set_state(
            initialization_data=initialization_data,
            initialization_actions=initialization_actions,
            message_history=full_trajectory,
        )
        predicted_tool_calls: list[ToolCall] = []
        for message in full_trajectory:
            if (
                isinstance(message, AssistantMessage)
                or isinstance(message, UserMessage)
            ) and message.is_tool_call():
                predicted_tool_calls.extend(message.tool_calls)

        # Setting up gold environment
        gold_environment = environment_constructor()
        gold_environment.set_state(
            initialization_data=initialization_data,
            initialization_actions=initialization_actions,
            message_history=message_history,
        )
        golden_actions = task.evaluation_criteria.actions or []
        for step_index, action in enumerate(golden_actions):
            agent_db_before_gold = (
                gold_environment.get_agent_db_state()
                if gold_environment.tools is not None
                else None
            )
            try:
                gold_environment.make_tool_call(
                    tool_name=action.name,
                    requestor=action.requestor,
                    **action.arguments,
                )
            except Exception as e:
                logger.warning(
                    f"Error in golden actions {action.name}({action.arguments}): {e}"
                )
            # Log each golden action's effect on agent DB to Logfire
            if (
                is_logfire_enabled()
                and agent_db_before_gold is not None
                and gold_environment.tools is not None
            ):
                try:
                    import logfire

                    agent_db_after_gold = gold_environment.get_agent_db_state()
                    diff = dict_diff_for_logging(
                        agent_db_before_gold, agent_db_after_gold
                    )
                    with logfire.span(
                        "agent_db_updated_gold",
                        task_id=task.id,
                        step_index=step_index,
                        tool_name=action.name,
                        tool_arguments=action.arguments,
                        agent_db_diff=diff,
                    ):
                        pass
                except Exception:
                    pass

        # Comparing the environments
        agent_db_hash = gold_environment.get_db_hash()
        user_db_hash = gold_environment.get_user_db_hash()
        predicted_agent_db_hash = predicted_environment.get_db_hash()
        predicted_user_db_hash = predicted_environment.get_user_db_hash()
        agent_db_match = agent_db_hash == predicted_agent_db_hash
        user_db_match = user_db_hash == predicted_user_db_hash
        if agent_db_match and user_db_match:
            db_reward = 1.0
            db_match = True
        else:
            db_reward = 0.0
            db_match = False
            # Log which side failed for debugging (agent vs user DB)
            if not agent_db_match:
                logger.debug(
                    f"DB check: agent DB mismatch (task_id={task.id})"
                )
            if not user_db_match:
                logger.debug(
                    f"DB check: user DB mismatch (task_id={task.id})"
                )

        # Log expected vs predicted DB state and diff to Logfire when enabled
        if is_logfire_enabled():
            try:
                import logfire

                expected_agent_db = gold_environment.get_agent_db_state()
                expected_user_db = gold_environment.get_user_db_state()
                predicted_agent_db = predicted_environment.get_agent_db_state()
                predicted_user_db = predicted_environment.get_user_db_state()
                agent_db_diff = dict_diff_for_logging(
                    expected_agent_db, predicted_agent_db
                )
                user_db_diff = dict_diff_for_logging(
                    expected_user_db, predicted_user_db
                )
                with logfire.span(
                    "db_check",
                    task_id=task.id,
                    db_match=db_match,
                    agent_db_match=agent_db_match,
                    user_db_match=user_db_match,
                    expected_agent_db_hash=agent_db_hash,
                    predicted_agent_db_hash=predicted_agent_db_hash,
                    expected_user_db_hash=user_db_hash,
                    predicted_user_db_hash=predicted_user_db_hash,
                    agent_db_diff=agent_db_diff,
                    user_db_diff=user_db_diff,
                    expected_agent_db_state=expected_agent_db,
                    predicted_agent_db_state=predicted_agent_db,
                    expected_user_db_state=expected_user_db,
                    predicted_user_db_state=predicted_user_db,
                ):
                    pass
            except Exception:
                pass

        db_check = DBCheck(db_match=db_match, db_reward=db_reward)

        # Run env assertions
        env_assertions = task.evaluation_criteria.env_assertions or []
        env_assertion_checks = []
        env_assertion_reward = 1.0
        for env_assertion in env_assertions:
            success = predicted_environment.run_env_assertion(
                env_assertion,
                raise_assertion_error=False,
            )
            res = EnvAssertionCheck(
                env_assertion=env_assertion,
                met=success,
                reward=1.0 if success else 0.0,
            )
            env_assertion_checks.append(res)
            env_assertion_reward *= res.reward

        reward = 1.0
        reward_breakdown = {}
        if RewardType.DB in task.evaluation_criteria.reward_basis:
            reward_breakdown[RewardType.DB] = db_reward
            reward *= db_reward
        if RewardType.ENV_ASSERTION in task.evaluation_criteria.reward_basis:
            reward_breakdown[RewardType.ENV_ASSERTION] = env_assertion_reward
            reward *= env_assertion_reward

        return RewardInfo(
            reward=reward,
            db_check=db_check,
            env_assertions=env_assertion_checks,
            reward_basis=task.evaluation_criteria.reward_basis,
            reward_breakdown=reward_breakdown,
        )
