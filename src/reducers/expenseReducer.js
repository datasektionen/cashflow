import * as types from '../actions/actionTypes';
import initialState from './initialState';

export default function expenseReducer(state = initialState.expense, action) {
    switch (action.type) {
        case types.LOAD_EXPENSE_SUCCESS:
            return {
                data: action.response,
                comments: state.comments
            };
        case types.LOAD_EXPENSE_COMMENTS_SUCCESS:
            return {
                data: state.data,
                comments: action.response.comments
            };
        default:
            return state;
    }
}