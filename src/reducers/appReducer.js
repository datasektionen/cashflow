import * as types from '../actions/actionTypes';
import initialState from './initialState';

export default function appReducer(state = initialState.app, action) {
    switch (action.type) {
        case types.LOAD_USER_SUCCESS:
            return {
                user: action.response.user,
                title: state.title
            };
        case types.SET_APP_TITLE:
            return {
                user: state.user,
                title: action.title
            };
        default:
            return state;
    }
}