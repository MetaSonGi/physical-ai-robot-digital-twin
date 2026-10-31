using System.Collections.Generic;
using RosMessageTypes.Sensor;
using RosMessageTypes.Std;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;

/// <summary>
/// Drives the imported OMX URDF (ArticulationBody chain) from /joint_states and
/// echoes the twin's actual joint positions on /unity/joint_states so ROS can
/// measure sync error and round-trip latency (see unity_bridge/twin_telemetry_node.py).
/// </summary>
public class RobotTwinController : MonoBehaviour
{
    [System.Serializable]
    public class JointBinding
    {
        public string rosJointName;           // e.g. "joint1"
        public ArticulationBody articulation; // drag the link from the imported URDF
        public bool prismatic;                // gripper fingers are prismatic (meters)
    }

    public string stateTopic = "/joint_states";
    public string echoTopic = "/unity/joint_states";
    public float echoHz = 20f;
    public List<JointBinding> joints = new List<JointBinding>();

    public float LastMessageAge { get; private set; } = float.PositiveInfinity;
    public IReadOnlyDictionary<string, double> LastState => lastState;

    ROSConnection ros;
    readonly Dictionary<string, double> lastState = new Dictionary<string, double>();
    TimeMsg lastStamp = new TimeMsg();
    float lastMsgTime = -1f, nextEcho;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<JointStateMsg>(stateTopic, OnJointState);
        ros.RegisterPublisher<JointStateMsg>(echoTopic);
    }

    void OnJointState(JointStateMsg msg)
    {
        for (int i = 0; i < msg.name.Length && i < msg.position.Length; i++)
            lastState[msg.name[i]] = msg.position[i];
        lastStamp = msg.header.stamp;
        lastMsgTime = Time.time;
    }

    void FixedUpdate()
    {
        foreach (var j in joints)
        {
            if (j.articulation == null || !lastState.TryGetValue(j.rosJointName, out var pos)) continue;
            var drive = j.articulation.xDrive;
            drive.target = j.prismatic ? (float)pos : (float)pos * Mathf.Rad2Deg; // ArticulationBody uses degrees
            j.articulation.xDrive = drive;
        }
    }

    void Update()
    {
        LastMessageAge = lastMsgTime < 0 ? float.PositiveInfinity : Time.time - lastMsgTime;
        if (Time.time < nextEcho || lastMsgTime < 0) return;
        nextEcho = Time.time + 1f / echoHz;

        var names = new string[joints.Count];
        var pos = new double[joints.Count];
        for (int i = 0; i < joints.Count; i++)
        {
            var j = joints[i];
            names[i] = j.rosJointName;
            float p = j.articulation != null && j.articulation.jointPosition.dofCount > 0 ? j.articulation.jointPosition[0] : 0f;
            pos[i] = p; // jointPosition is already in radians / meters
        }
        // Echo the original stamp so ROS can compute ROS->Unity->ROS latency.
        var msg = new JointStateMsg { header = new HeaderMsg { stamp = lastStamp }, name = names, position = pos };
        ros.Publish(echoTopic, msg);
    }
}
