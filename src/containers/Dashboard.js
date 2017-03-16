import React, { Component } from 'react';
import Paper from 'material-ui/Paper';
import Container from 'muicss/lib/react/container';
import Row from 'muicss/lib/react/row';
import Col from 'muicss/lib/react/col';

class Dashboard extends Component {
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

export default Dashboard;