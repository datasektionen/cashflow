import * as types from '../actions/actionTypes';
import initialState from './initialState';

export default function appReducer(state = initialState.app, action) {
    switch (action.type) {
        case types.LOAD_USER_SUCCESS:
            return {
                user: action.response.user,
                title: state.title,
                message: state.message,
                snack: false
            };

        case types.SET_APP_TITLE:
            return {
                user: state.user,
                title: action.title,
                message: state.message,
                snack: false
            };

        case types.EXPENSE_UPLOAD:
            return makeSnackbar("Laddar upp kvitto...", state);

        case types.PROFILE_SUBMIT_SUCCESS:
            return makeSnackbar("Profilen uppdaterades!", state);

        default:
            return state;
    }
}

function makeSnackbar(message, state) {
    const newState = Object.assign({}, state);

    newState.message = message;
    newState.snack = true;

    return newState;
}