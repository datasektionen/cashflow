import * as types from '../actions/actionTypes';
import initialState from './initialState';

export default function expenseReducer(state = initialState.expense, action) {
    switch (action.type) {
        case types.LOAD_EXPENSE_SUCCESS:
            return action.response;
        case types.LOAD_EXPENSE_COMMENTS_SUCCESS:
            return action.response.comments;
        default:
            return state;
    }
}