import { combineReducers } from 'redux';
import expensesReducer from './expensesReducer';
import expenseReducer from './expenseReducer';
import appReducer from './appReducer';

const rootReducer = combineReducers({
    app: appReducer,
    expenses: expensesReducer,
    expense: expenseReducer
});

export default rootReducer;