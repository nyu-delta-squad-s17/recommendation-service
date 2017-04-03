from behave import *
import json
import server


@when(u'I visit the "home page"')
def step_impl(context):
    context.resp = context.app.get('/')


@then(u'I should see "{message}"')
def step_impl(context, message):
    assert message in context.resp.data


@then(u'I should not see "{message}"')
def step_impl(context, message):
    assert message not in context.resp.data


@given(u'the following products')
def step_impl(context):
    # server.data_reset()
    server.conn.execute("TRUNCATE TABLE `recommendations`")
    for row in context.table:
        server.conn.execute("INSERT INTO `recommendations` VALUES (%d, %d, %d,\
                '%s\', %d)" % (int(row["id"]), int(row["parent_product_id"]),
                               int(row["related_product_id"]), row["type"],
                               int(row["priority"])))


@when(u'I visit "{url}"')
def step_impl(context, url):
    context.resp = context.app.get(url)
    assert context.resp.status_code == 200

