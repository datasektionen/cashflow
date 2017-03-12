# Cashflow 2.0

## API documentation

### Creating a new expense
Method: `PUT`<br>
URL: `/api/expense/new/`

**Request:**
json:
```
{

}
```

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
      "owner_first_name":"John",
      "reimbursement":null,
      "description":"Foo",
      "owner_last_name":"Doe",
      "expense_date":"2017-03-05",
      "verification":"E231",
      "expense_parts":[
         {
            "budget_line":{
               "budget_line_name":"mat",
               "cost_centre":{
                  "cost_centre_name":"dwrek",
                  "committee":{
                     "committee_name":"Drek",
                     "committee_id":1
                  },
                  "cost_centre_id":2
               },
               "budget_line_id":3
            },
            "attest_date":"2017-03-06",
            "amount":12,
            "attested_by":"foba",
            "id":5
         }
      ],
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

**Responese:**
```
{
    "expenses": [<List of expenses>]
}
```

### Getting all expenses belonging to user
Method: `GET`<br>
URL: `/api/user/<username>/expenses/`

Retrieves all expenses belonging to the user with the specified `kthid`/`username`.

**Responese:**
```
{
    "expenses": [<List of expenses>]
}
```


### Get all unattested expenses

Method: `GET`<br>
URL: `/api/attest/`

Retrieves all the expenses that the current user can attest that haven't been attested yet.

**Responese:**
```
{"expenses": [<List of expenses>]
```

### Attest expense
Method: `POST`<br>
URL: `/api/attest/`

Attest all the specified reciepts

**Request:**
list:
```
[1,22,23,12]
```

**Response:**
```
{
  'success': true
}
```

### Get current user
Method: `GET`<br>
URL: `/api/user/`

Get the currently logged in

**Response:**
```
{
   "user":{
      "username":"foba",
      "bank_name":"Swedbank",
      "first_name":"Foo",
      "last_name":"Bar",
      "sorting_number":"2322-1",
      "default_account":{
         "id":1,
         "name":"DKM"
      },
      "bank_account":"2131231231"
   }
}
```

### Get user
Method: `GET`<br>
URL: `/api/user/<username>/`

Get a user by its `kthid`/`username`

**Response:**
```
{
   "user":{
      "username":"foba",
      "bank_name":"Swedbank",
      "first_name":"Foo",
      "last_name":"Bar",
      "sorting_number":"2322-1",
      "default_account":{
         "id":1,
         "name":"DKM"
      },
      "bank_account":"2131231231"
   }
}
```

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
                  },
                  {
                     "budget_line_name":"Representation",
                     "budget_line_id":2
                  }
               ]
            }
         ]
      }
   ]
}
```