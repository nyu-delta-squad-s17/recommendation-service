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

Scenario: Create a recommendation
	When I create "/recommendations" with parent product "9", related product "5", type "x-sell", and priority "2"
	And I visit "/recommendations"
	Then I should see "9"
  
Scenario: Delete a recommendation
    When I delete "/recommendations" with id "3"
    And I visit "/recommendations"
    Then I should see "1"
    And I should see "2"
    And I should not see "4"

Scenario: Read single recommendation
	When I visit the "/recommendations" with id "1"
	Then I should see "1"

Scenario: Click a recommendation
	When I click the "/recommendations" with id "1"
	Then I should see "4"
	And I should not see "5"

Scenario: Read recommendation with query parameter type
	When I click "/recommendations" with type "'x-sell'"
	Then I should see "x-sell"
	And I should not see "up-sell"

Scenario: Read recommendation with query parameter product-id
	When I click "/recommendations" with product-id "2"
	Then I should see "up-sell"
	And I should not see "1"

Scenario: Update a recommendation
	When I update "/recommendations" with id "2" and parent product "1", related product "3", type "up-sell", and priority "8"
	And I visit "/recommendations"
	Then I should see "8"
