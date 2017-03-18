import * as types from '../actions/actionTypes';
import initialState from './initialState';

export default function profileReducer(state = initialState.profile, action) {
    switch (action.type) {
        case types.LOAD_PROFILE_SUCCESS:
            return action.response.user;
        case types.PROFILE_MODEL_CHANGE:
            const newState = Object.assign({}, state);
            newState[action.element] = action.newValue;
            return newState;
        default:
            return state;
    }
}