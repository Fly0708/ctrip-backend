import os
from typing import TypedDict

from typing_extensions import Annotated
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek

from app.database import CtripFlight

flight_table = """
CREATE TABLE `ctrip_flight` (
  `id` int NOT NULL AUTO_INCREMENT,
  `task_id` bigint DEFAULT NULL,
  `data_time` datetime NOT NULL,
  `day` date NOT NULL comment '日期',
  `airline_name` varchar(255) DEFAULT NULL,
  `flight_no` varchar(255) DEFAULT NULL comment '航班号',
  `aircraft_name` varchar(255) DEFAULT NULL comment '飞机型号名称',
  `operate_airline_name` varchar(255) DEFAULT NULL comment '航班公司名称',
  `departure_city_name` varchar(255) DEFAULT NULL comment '出发城市名称',
  `departure_airport_name` varchar(255) DEFAULT NULL comment '出发机场名称',
  `arrival_city_name` varchar(255) DEFAULT NULL comment '到达城市名称',
  `arrival_airport_name` varchar(255) DEFAULT NULL comment '到达机场名称',
  `adult_price` varchar(255) DEFAULT NULL comment '价格',
  `discount_rate` varchar(255) DEFAULT NULL comment '折扣率',
  `is_latest` tinyint(1) NOT NULL DEFAULT '0',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) comment '航班信息表';
"""

prompt_template = ChatPromptTemplate([
    ('system', """
    Given an input question, create a syntactically correct {dialect} query to run to help find the answer. Please note that your answer should only output sql text, dont need markdown format. Unless the user specifies in his question a specific number of examples they wish to obtain, always limit your query to at most {top_k} results. You can order the results by a relevant column to return the most interesting examples in the database.

Never query for all the columns from a specific table, only ask for a the few relevant columns given the question.

Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.

Only use the following tables:
{table_info}

Question: {input}
    """),

])

gen_output_template = ChatPromptTemplate([('system', """这是一个航班推荐引擎，请根据下方用户的输入 结合 下方数据库的查询结果, 给出一个航班推荐结果.
用户输入:{input}
所查询表的结构:
{table_info}
数据库查询结果信息:
{db_query_results}
""")])


class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]


from pydantic import BaseModel, Field


class SqlResult(BaseModel):
    '''Joke to tell user.'''

    sql: str = Field(description="查询sql")


llm = ChatDeepSeek(
    model="deepseek-chat",
    max_tokens=None,
    timeout=None,
    max_retries=0,
    api_key= os.getenv("DEEPSEEK_API_KEY"),
)


def get_flight_query_sql(user_input: str) -> (str,):
    if not user_input:
        raise ValueError("user_input is empty")

    prompt = prompt_template.invoke(
        {
            "dialect": 'mysql',
            "top_k": 10,
            "table_info": flight_table,
            "input": user_input,
        }
    )

    structured_llm = llm.with_structured_output(SqlResult)
    result = structured_llm.invoke(prompt)
    return result.sql


# 根据数据库查询结果 美化输出
def gen_output_by_data(user_input: str, data) -> str:
    prompt = gen_output_template.invoke(
        {
            "db_query_results": data,
            "table_info": flight_table,
            "input": user_input,
        }
    )
    result = llm.invoke(prompt).content
    print(result)
    return result
