import * as types from '../actions/actionTypes';
import initialState from './initialState';

export default function (state = initialState.expenses, action) {
    switch (action.type) {
        case types.LOAD_EXPENSES_SUCCESS:
            return action.expenses;
        default:
            return state;
    }
}