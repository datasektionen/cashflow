import React, { Component, PropTypes } from 'react';
import Paper from 'material-ui/Paper';
import Container from 'muicss/lib/react/container';
import Row from 'muicss/lib/react/row';
import Col from 'muicss/lib/react/col';
import { SET_APP_TITLE } from '../actions/actionTypes';
import { connect } from "react-redux";

class Dashboard extends Component {
    componentWillMount () {
        this.props.setTitle();
    }

    render () {
        return (
            <Container fluid={true}>
                <Row>
                    <Col md="8">
                        <Paper zDepth={1}>
                            <h2>Welcome to the Dashboard!</h2>
                        </Paper>
                    </Col>
                    <Col md="4">
                        <Paper zDepth={1} style={{height: "80vh"}}>
                            <h2>möp</h2>
                        </Paper>
                    </Col>
                </Row>
            </Container>
        );
    }
}

Dashboard.propTypes = {
    setTitle: PropTypes.func.isRequired
};


function mapStateToProps () {
    return {}
}

function mapDispatchToProps(dispatch) {
    return {
        setTitle: () => dispatch({ type: SET_APP_TITLE, title: 'Översikt' })
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(Dashboard);