using RosMessageTypes.Std;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;

/// <summary>Space bar (or UI button -> Toggle()) latches /safety/estop.</summary>
public class EStopButton : MonoBehaviour
{
    public KeyCode key = KeyCode.Space;
    bool engaged;
    ROSConnection ros;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<BoolMsg>("/safety/estop");
    }

    void Update() { if (Input.GetKeyDown(key)) Toggle(); }

    public void Toggle()
    {
        engaged = !engaged;
        ros.Publish("/safety/estop", new BoolMsg(engaged));
        Debug.Log($"E-STOP {(engaged ? "ENGAGED" : "released")}");
    }
}
