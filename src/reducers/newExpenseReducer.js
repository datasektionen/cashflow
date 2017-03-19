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
                costCentres: state.costCentres,
                step: state.step
            };

        case types.ADD_EXPENSE_PART:
            const expandedParts = [].concat(state.parts, action.part);

            return {
                data: {
                    description: state.data.description,
                    date: state.data.date,
                    amount: 0
                },
                parts: expandedParts,
                committees: state.committees,
                costCentres: state.costCentres,
                step: state.step
            };

        case types.LOAD_COST_CENTRES_SUCCESS:
            return {
                data: state.data,
                parts: state.parts,
                committees: state.committees,
                costCentres: action.response.cost_centres,
                step: state.step
            };

        case types.LOAD_COMMITTEES_SUCCESS:
            return {
                data: state.data,
                parts: state.parts,
                committees: action.response.committees,
                costCentres: state.costCentres,
                step: state.step
            };

        case types.RESET_NEW_EXPENSE:
            const reset = Object.assign({}, initialState.newExpense);
            reset.committees = state.committees;
            return reset;

        case types.NEW_EXPENSE_SUBMIT_SUCCESS:
            const data = Object.assign({}, state.data);
            data.expense_id = action.response.expense.id;

            return {
                data: data,
                parts: state.parts,
                committees: state.committees,
                costCentres: state.costCentres,
                step: 1
            };

        case types.EXPENSE_UPLOAD_SUCCESS:
            return {
                data: state.data,
                parts: state.parts,
                committees: state.committees,
                costCentres: state.costCentres,
                step: 2
            };

        default:
            return state;
    }
}