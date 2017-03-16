import * as types from '../actions/actionTypes';
import initialState from './initialState';

export default function expensesReducer(state = initialState.expenses, action) {
    switch (action.type) {
        case types.LOAD_EXPENSES_SUCCESS:
            console.log("Wät");
            return action.response.expenses;
        default:
            return state;
    }
}