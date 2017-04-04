Feature: The recommendation service back-end
    As a user of the platform
    I need a RESTful recommendation service
    So that I can get product recommendations for either products I've bought or is interested in.

Background:
	Given the following products
		| id | parent_product_id | related_product_id | type    | priority |
		|  1 |                 1 |                  2 | x-sell  |        5 |
		|  2 |                 1 |                  3 | up-sell |        5 |
		|  3 |                 2 |                  4 | up-sell |        5 |

Scenario: Running server
	When I visit the "home page"
	Then I should see "Recommendations REST API Service"
	And I should not see "404 Not Found"

Scenario: List all recommendations
	When I visit "/recommendations"
	Then I should see "1"
	And I should see "2"
	And I should see "3"

Scenario: Delete a recommendation
    When I delete "/recommendations" with id "3"
    And I visit "/recommendations"
    Then I should see "1"
    And I should see "2"
    And I should not see "4"