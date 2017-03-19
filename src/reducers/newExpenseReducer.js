import * as types from '../actions/actionTypes';
import initialState from './initialState';

export default function newExpenseReducer(state = initialState.newExpense, action) {
    switch (action.type) {
        case types.NEW_EXPENSE_MODEL_CHANGE:
            const newState = Object.assign({}, state.data);
            newState[action.element] = action.newValue;

            return {
                data: newState,
                parts: state.parts,
                committees: state.committees,
                costCentres: state.costCentres
            };
        case types.LOAD_COST_CENTRES_SUCCESS:
            return {
                data: state.data,
                parts: state.parts,
                committees: state.committees,
                costCentres: action.response.cost_centres
            };
        case types.LOAD_COMMITTEES_SUCCESS:
            return {
                data: state.data,
                parts: state.parts,
                committees: action.response.committees,
                costCentres: state.costCentres
            };
        default:
            return state;
    }
}