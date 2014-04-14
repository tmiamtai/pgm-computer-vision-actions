from pylab import *

# Karol's C++ program will gather data and compute errors. This must only
# deal with probabilities, etc.

# TODO
# joint distribution
# mixture distribution
# parallelize
# expectation
# entropy
# check for bugs

# or a function to set these
objects = ['book1', 'book2', 'book3']
poses = ['up-forward', 'up-backward', 'down-forward', 'down-backward']


def pose2vec(name):
    vec = zeros(len(poses))
    vec[poses.index(name)] = 1
    return vec


def vec2pose(vec):
    return poses[vec.index(1)]

actions = ['stay', 'flip', 'rotate', 'flipRotate']

stay = eye(4)
flip = zeros([4, 4])
flip[0, 2] = flip[1, 3] = flip[2, 0] = flip[3, 1] = 1
rotate = zeros([4, 4])
rotate[0, 1] = rotate[1, 0] = rotate[2, 3] = rotate[3, 2] = 1
flipRotate = eye(4)[::-1]


def action2mat(name):
    if name == 'stay':
        return stay
    elif name == 'flip':
        return flip
    elif name == 'rotate':
        return rotate
    elif name == 'flipRotate':
        return flipRotate
    else:
        raise "invalid action name, " + name


def mat2action(mat):
    if array_equal(mat, stay):
        return'stay':
    elif array_equal(mat, flip):
        return'flip':
        elif array_equal(mat, rotate):
        return'rotate':
    elif array_equal(mat, flipRotate):
        return'flipRotate':
    else:
        raise "invalid action matrix, " + str(mat)


def train(errors):
    # errors = array[object][pose][feature][sample]
    # save the errors. train in real time

    global nObjects, nPoses, nFeatures, nTrainingSamples, nActions, nObservations
    nObjects, nPoses, nFeatures, nTrainingSamples = errors.shape
    nActions = nObservations = nPoses

    global trainingErrors
    trainingErrors = errors


class memorize(dict):
    # cache function calls

    def __init__(self, func):
        self.func = func

    def __call__(self, *args):
        return self[args]

    def __missing__(self, key):
        result = self[key] = self.func(*key)
        return result


@memorize
def nextPoseIdx(idxPreviousPose, idxAction):
    actionName = actions[idxAction]
    previousPoseName = poses[idxPreviousPose]
    nextPoseVec = inner(action2mat(actionName), pose2vec(previousPoseName))
    nextPoseName = vec2pose(nextPoseVec)
    return poses.index(nextPoseName)


@memorize
def previousPoseIdx(idxNextPose, idxAction):
    actionName = actions[idxAction]
    nextPoseName = poses[idxNextPose]
    prevPoseVec = inner(inv(action2mat(actionName)), pose2vec(nextPoseName))
    prevPoseName = vec2pose(prevPoseVec)
    return poses.index(prevPoseName)


class Distribution:

    def __init__(self, values):
        # learn

    def prob(self, value):
        pass

    def expectedValue(self):
        pass


@memorize
def dfgop(idxObject, idxPose, idxFeature):
    # likelihood distribution
    return Distribution(errors[idxObject, idxPose, idxFeature, :])


@memorize
def dFgop(idxObject, idxPose):
    # likelihood joint distribution
    return prod([dfgop(idxObject, idxPose, idxFeature) for idxFeature in range(nFeatures)])


observationHistory = []
objectProbHistory = []
actionHistory = [None]


def observe(error):
    global observationHistory
    idxObservation = len(observationHistory)
    observationHistory.append(error)
    objectProbHistory.append(posterior_O_prob(idxObservation))
    # TODO
    # compute expectation
    # compute entropy
    # determine the best action


@memorize
def pop():
    # prior
    return 1.0 / float(nObjects * nPoses)


@memorize
def pfgop(idxObservation, idxObject, idxPose, idxFeature):
    # likelihood probability
    return dfgop(idxObject, idxPose, idxFeature).prob(observationHistory[idxObservation][idxFeature])


@memorize
def pFgop(idxObservation, idxObject, idxPose):
    # likelihood joint probability
    return dFgop(idxObject, idxPose).prob(observationHistory[idxObservation])


@memorize
def pF(idxObservation):
    # evidence for the first observation.
    # also shows the novelty of the features found
    return pop() * sum([pFgop(idxObservation, idxObject, idxPose) for idxObject, idxPose in zip(range(len(objects)), range(len(poses)))])
    pass


@memorize
def posterior_op_prob(idxObservation, idxObject, idxPose):
    if idxObservation == 0:
        return pop() * pFgop(idxObservation, idxObject, idxPose) / pF(idxObservation)
    else:
        posterior_op_dist(idxObservation, idxObject,
                          idxPose, actionHistory(idxObservation)).prob(idxObservation)


@memorize
def posterior_o_prob(idxObservation, idxObject):
    if idxObservation == 0:
        return sum([posterior_op_prob(idxObservation, idxObject, idxPose) for idxPose in range(nPoses)])
    else:
        posterior_o_dist(idxObservation, idxObject,
                         actionHistory(idxObservation)).prob(idxObservation)


@memorize
def posterior_O_prob(idxObservation):
    # distribution of object probabilities
    return [posterior_o_prob(idxObservation, idxObject) for idxObject in range(nObjects)]


@memorize
def posterior_op_dist(idxObservation, idxObject, idxPose, idxAction):
    fromPoseIdx = previousPoseIdx(idxPose, idxAction)
    lastPosterior = posterior_op_prob(
        idxObservation - 1, idxObject, fromPoseIdx)
    likelihoodDistribution = dFgop(idxObservation, idxObject, idxPose)
    evidenceDistribution = evidence_dist(idxObservation)
    return lastPosterior * likelihoodDistribution / evidenceDistribution


@memorize
def posterior_o_dist(idxObservation, idxObject, idxAction):
    return sum([posterior_op_dist(idxObservation, idxObject, idxPose, idxAction) for idxPose in range(nPoses)])


@memorize
def evidence_dist(idxObservation):
    accumulate = []
    for idxPose in range(len(poses)):
        for idxAction in range(len(actions)):
            for idxObject in range(len(objects)):
                fromPoseIdx = previousPoseIdx(idxPose, idxAction)
                lastPosterior = posterior_op_prob(
                    idxObservation - 1, idxObject, fromPoseIdx)
                likelihoodDistribution = dFgop(
                    idxObservation, idxObject, idxPose)
                accumulate.append(lastPosterior * likelihoodDistribution)
    return sum(accumulate)
 
