import * as types from '../actions/actionTypes';
import initialState from './initialState';

export default function newExpenseReducer(state = initialState.newExpense, action) {
    switch (action.type) {
        case types.NEW_EXPENSE_MODEL_CHANGE:
            const newState = Object.assign({}, state);
            newState[action.element] = action.newValue;
            return newState;
        default:
            return state;
    }
}