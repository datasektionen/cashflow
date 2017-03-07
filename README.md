# Cashflow 2.0

## API documentation

### Creating a new expense
Method: `PUT`<br>
URL: `/api/expense/new/`

### Updating expense
Method: `PUT`<br>
URL: `/api/expense/<id>/`


### Getting expense by id
Method: `GET`<br>
URL: `/api/expense/<id>/`

Get a `expense` by its `id`, also retrieves `expense_parts` and `budget_lines` associated with the expense.

<br>

**Response:**
```
{
   "expense":{
      "reimbursement":1,
      "description": "Mat vid arbetsmöte",
      "parts": [
         {
            "budget_line":{
               "budget_line_name":"MUTA",
               "budget_line_id":1,
               "cost_centre":{
                  "cost_centre_name":"Allmänt",
                  "cost_centre_id":1,
                  "committee":{
                     "committee_name":"D-rektoratet",
                     "committee_id":1
                  }
               }
            },
            "attest_date":"2017-03-06",
            "amount":100,
            "attested_by":1,
            "attested_by_username":"foba"
            "expense":1,
            "id":3
         }
      ],
      "expense_date":"2017-03-05",
      "verification":"E231",
      "owner":2,
      "id":1,
      "owner_username":"johdo"
   }
}
```


### Getting all expenses
Method: `GET`<br>
URL: `/api/expense/`

Retrieves all expenses current user is elegible to view



### Get user
Method: `GET`<br>
URL: `/api/user/<`username`>/`

Get a user by its `kthid`/`username`,

**Response:**


### Get budget
Method: `GET`<br>
URL: `/api/budget/`


**Response:**
```
{
   "committees":[
      {
         "committee_name":"D-rektoratet",
         "committee_id":1,
         "cost_centres":[
            {
               "cost_centre_name":"Allmänt",
               "cost_centre_id":1,
               "budget_lines":[
                  {
                     "budget_line_name":"MUTA",
                     "budget_line_id":1
                  }
               ]
            }
         ]
      }
   ]
}
```