import { combineReducers } from 'redux';
import expensesReducer from './expensesReducer';

const rootReducer = combineReducers({
    expensesReducer
});

export default rootReducer;