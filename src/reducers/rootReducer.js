import { combineReducers } from 'redux';
import expensesReducer from './expensesReducer';
import expenseReducer from './expenseReducer';

const rootReducer = combineReducers({
    expensesReducer,
    expenseReducer
});

export default rootReducer;