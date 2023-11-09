import os
import signal
import sys
import time

import example_robot_data
import numpy as np
import pinocchio

import crocoddyl

WITHDISPLAY = "display" in sys.argv or "CROCODDYL_DISPLAY" in os.environ
WITHPLOT = "plot" in sys.argv or "CROCODDYL_PLOT" in os.environ
signal.signal(signal.SIGINT, signal.SIG_DFL)

hector = example_robot_data.load("hector")
robot_model = hector.model

target_pos = np.array([1.0, 0.0, 1.0])
target_quat = pinocchio.Quaternion(1.0, 0.0, 0.0, 0.0)

state = crocoddyl.StateMultibody(robot_model)

d_cog, cf, cm, u_lim, l_lim = 0.1525, 6.6e-5, 1e-6, 5.0, 0.1
tau_f = np.array(
    [
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 1.0],
        [0.0, d_cog, 0.0, -d_cog],
        [-d_cog, 0.0, d_cog, 0.0],
        [-cm / cf, cm / cf, -cm / cf, cm / cf],
    ]
)
actuation = crocoddyl.ActuationModelMultiCopterBase(state, tau_f)

nu = state.nv
runningCostModel = crocoddyl.CostModelSum(state, nu)
terminalCostModel = crocoddyl.CostModelSum(state, nu)

# Costs
xResidual = crocoddyl.ResidualModelState(state, state.zero(), nu)
xActivation = crocoddyl.ActivationModelWeightedQuad(
    np.array([0.1] * 3 + [1000.0] * 3 + [1000.0] * robot_model.nv)
)
uResidual = crocoddyl.ResidualModelJointEffort(state, actuation, nu)
xRegCost = crocoddyl.CostModelResidual(state, xActivation, xResidual)
uRegCost = crocoddyl.CostModelResidual(state, uResidual)
goalTrackingResidual = crocoddyl.ResidualModelFramePlacement(
    state,
    robot_model.getFrameId("base_link"),
    pinocchio.SE3(target_quat.matrix(), target_pos),
    nu,
)
goalTrackingCost = crocoddyl.CostModelResidual(state, goalTrackingResidual)
runningCostModel.addCost("xReg", xRegCost, 1e-6)
runningCostModel.addCost("uReg", uRegCost, 1e-6)
runningCostModel.addCost("trackPose", goalTrackingCost, 1e-2)
terminalCostModel.addCost("goalPose", goalTrackingCost, 3.0)

dt = 3e-2
runningModel = crocoddyl.IntegratedActionModelEuler(
    crocoddyl.DifferentialActionModelFreeInvDynamics(
        state, actuation, runningCostModel
    ),
    dt,
)
terminalModel = crocoddyl.IntegratedActionModelEuler(
    crocoddyl.DifferentialActionModelFreeInvDynamics(
        state, actuation, terminalCostModel
    ),
    dt,
)

# Creating the shooting problem and the solver
T = 33
problem = crocoddyl.ShootingProblem(
    np.concatenate([hector.q0, np.zeros(state.nv)]), [runningModel] * T, terminalModel
)
solver = crocoddyl.SolverIntro(problem)

solver.setCallbacks([crocoddyl.CallbackLogger(), crocoddyl.CallbackVerbose()])

cameraTF = [-0.03, 4.4, 2.3, -0.02, 0.56, 0.83, -0.03]
if WITHDISPLAY:
    try:
        import gepetto

        gepetto.corbaserver.Client()
        display = crocoddyl.GepettoDisplay(hector, 4, 4, cameraTF, floor=False)
        hector.viewer.gui.addXYZaxis("world/wp", [1.0, 0.0, 0.0, 1.0], 0.03, 0.5)
        hector.viewer.gui.applyConfiguration(
            "world/wp",
            [
                *target_pos.tolist(),
                target_quat[0],
                target_quat[1],
                target_quat[2],
                target_quat[3],
            ],
        )
        if WITHPLOT:
            solver.setCallbacks(
                [
                    crocoddyl.CallbackVerbose(),
                    crocoddyl.CallbackLogger(),
                    crocoddyl.CallbackDisplay(display),
                ]
            )
        else:
            solver.setCallbacks(
                [crocoddyl.CallbackVerbose(), crocoddyl.CallbackDisplay(display)]
            )
    except Exception:
        display = crocoddyl.MeshcatDisplay(hector)
if WITHPLOT:
    solver.setCallbacks(
        [
            crocoddyl.CallbackVerbose(),
            crocoddyl.CallbackLogger(),
        ]
    )
else:
    solver.setCallbacks([crocoddyl.CallbackVerbose()])

# Solving the problem with the solver
solver.solve()

# Plotting the entire motion
if WITHPLOT:
    log = solver.getCallbacks()[1]
    crocoddyl.plotOCSolution(
        solver.xs,
        [d.differential.multibody.joint.tau for d in solver.problem.runningDatas],
        figIndex=1,
        show=False,
    )
    crocoddyl.plotConvergence(
        log.costs, log.pregs, log.dregs, log.stops, log.grads, log.steps, figIndex=2
    )

# Display the entire motion
if WITHDISPLAY:
    display.rate = -1
    display.freq = 1
    while True:
        display.displayFromSolver(solver)
        time.sleep(1.0)
