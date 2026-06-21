import "./index.css";
import { Composition } from "remotion";
import { VmListDemo, VmShowDemo, NodeListDemo, ClusterCephDemo, YamlSpecDemo } from "./Composition";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="vm-list"
        component={VmListDemo}
        durationInFrames={160}
        fps={30}
        width={940}
        height={390}
      />
      <Composition
        id="vm-show"
        component={VmShowDemo}
        durationInFrames={140}
        fps={30}
        width={600}
        height={420}
      />
      <Composition
        id="node-list"
        component={NodeListDemo}
        durationInFrames={130}
        fps={30}
        width={880}
        height={330}
      />
      <Composition
        id="cluster"
        component={ClusterCephDemo}
        durationInFrames={100}
        fps={30}
        width={940}
        height={340}
      />
      <Composition
        id="yaml-spec"
        component={YamlSpecDemo}
        durationInFrames={150}
        fps={30}
        width={1050}
        height={470}
      />
    </>
  );
};
