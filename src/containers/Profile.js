import React, {Component, PropTypes} from "react";
import {bindActionCreators} from "redux";
import * as ProfileActions from "../actions/ProfileActions";
import {connect} from "react-redux";

import {SET_APP_TITLE} from "../actions/actionTypes";

import Subheader from "material-ui/Subheader";
import Paper from "material-ui/Paper";
import TextField from "material-ui/TextField";
import Divider from "material-ui/Divider";

import Col from "muicss/lib/react/col";
import Row from "muicss/lib/react/row";
import Container from "muicss/lib/react/container";

class Profile extends Component {

    componentWillMount () {
        this.props.actions.loadProfile();
        this.props.setTitle();
    }

    render () {
        // const { profile } = this.props;
        const profile = this.props.profile;
        const textFieldChange = this.props.actions.textFieldChange;
        const style = {
            marginLeft: 20
        };
        const containerStyle = {
            marginBottom: 1
        };

        return (
            <div>
                <Subheader>Profiluppgifter från KTH CAS</Subheader>

                <Paper zDepth={1}>
                    <Container fluid={true} style={containerStyle}>
                        <Row>
                            <Col md="6">
                                <TextField
                                    style={style}
                                    floatingLabelText="Förnamn"
                                    floatingLabelFixed={true}
                                    underlineShow={false}
                                    fullWidth={true}
                                    disabled={true}
                                    value={profile.first_name}
                                />
                            </Col>
                            <Col md="6">
                                <TextField
                                    style={style}
                                    floatingLabelText="Efternamn"
                                    floatingLabelFixed={true}
                                    underlineShow={false}
                                    disabled={true}
                                    fullWidth={true}
                                    value={profile.last_name}
                                />
                            </Col>
                        </Row>
                    </Container>
                    <Divider />
                    <Container fluid={true} style={containerStyle}>
                        <Row>
                            <Col md="6">
                                <TextField
                                    style={style}
                                    floatingLabelText="E-postadress"
                                    floatingLabelFixed={true}
                                    underlineShow={false}
                                    disabled={true}
                                    fullWidth={true}
                                    value={profile.username + "@kth.se"}
                                />
                            </Col>
                            <Col md="6">
                                <TextField
                                    style={style}
                                    floatingLabelText="Förvalt bankkonto"
                                    floatingLabelFixed={true}
                                    underlineShow={false}
                                    disabled={true}
                                    fullWidth={true}
                                    value={profile.default_account.name}
                                />
                            </Col>
                        </Row>
                    </Container>
                </Paper>

                <Subheader>Bankuppgifter</Subheader>

                <Paper zDepth={1}>
                    <TextField
                        style={style}
                        fullWidth={true}
                        hintText="Cerisa Banken"
                        value={profile.bank_name}
                        floatingLabelText="Bank"
                        underlineShow={false}
                        onChange={(e, n) => textFieldChange('bank_name', n)}
                    />
                    <Divider />
                    <Container fluid={true} style={containerStyle}>
                        <Row>
                            <Col md="6">
                                <TextField
                                    style={style}
                                    floatingLabelText="Clearingnummer"
                                    floatingLabelFixed={true}
                                    underlineShow={false}
                                    hintText={1234}
                                    type="number"
                                    fullWidth={true}
                                    value={profile.sorting_number}
                                    onChange={(e, n) => textFieldChange('sorting_number', n)}
                                />
                            </Col>
                            <Col md="6">
                                <TextField
                                    style={style}
                                    floatingLabelText="Bankkontonummer"
                                    value={profile.bank_account}
                                    floatingLabelFixed={true}
                                    fullWidth={true}
                                    underlineShow={false}
                                    onChange={(e, n) => textFieldChange('bank_account', n)}
                                />
                            </Col>
                        </Row>
                    </Container>
                </Paper>
            </div>
        );
    }
}

Profile.propTypes = {
    profile: PropTypes.object.isRequired,
    actions: PropTypes.object.isRequired
};

function mapStateToProps (state) {
    return {
        profile: state.profile
    }
}

function mapDispatchToProps(dispatch) {
    return {
        setTitle: () => dispatch({ type: SET_APP_TITLE, title: 'Redigera min profil' }),
        actions: bindActionCreators(ProfileActions, dispatch)
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(Profile);