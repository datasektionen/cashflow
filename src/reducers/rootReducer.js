import { combineReducers } from 'redux';
import expensesReducer from './expensesReducer';

const rootReducer = combineReducers({
    expensesReducer: expensesReducer
});

export default rootReducer;