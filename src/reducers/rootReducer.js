import { combineReducers } from 'redux';
import expensesReducer from './expensesReducer';
import expenseReducer from './expenseReducer';
import appReducer from './appReducer';
import profileReducer from './profileReducer';
import newExpenseReducer from './newExpenseReducer';

const rootReducer = combineReducers({
    app: appReducer,
    expenses: expensesReducer,
    expense: expenseReducer,
    profile: profileReducer,
    newExpense: newExpenseReducer
});

export default rootReducer;