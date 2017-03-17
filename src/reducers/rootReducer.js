import { combineReducers } from 'redux';
import expensesReducer from './expensesReducer';
import expenseReducer from './expenseReducer';
import appReducer from './appReducer';

const rootReducer = combineReducers({
    appReducer,
    expensesReducer,
    expenseReducer
});

export default rootReducer;