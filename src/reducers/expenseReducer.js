import * as types from '../actions/actionTypes';
import initialState from './initialState';

export default function expenseReducer(state = initialState.expense, action) {
    switch (action.type) {
        case types.LOAD_EXPENSE_SUCCESS:
            return {
                data: action.response,
                comments: state.comments,
                files: state.files
            };

        case types.LOAD_EXPENSE_COMMENTS_SUCCESS:
            return {
                data: state.data,
                comments: action.response.comments,
                files: state.files
            };

        case types.LOAD_EXPENSE_FILES_SUCCESS:
            return {
                data: state.data,
                comments: state.comments,
                files: action.response.files
            };

        default:
            return state;
    }
}