/* @jsx React.createElement */

function SkelLine({ w = "100%", h = 10 }) {
  return <span className="skel-line" style={{ width: w, height: h }}/>;
}

function SkelTile() {
  return (
    <div className="product-tile skel">
      <div className="product-thumb skel-block"/>
      <div className="product-meta">
        <SkelLine w="40%" h={8}/>
        <SkelLine w="85%" h={12}/>
        <SkelLine w="55%" h={8}/>
      </div>
    </div>
  );
}

function SkelRecCard() {
  return (
    <div className="rec-card skel">
      <div className="rec-thumb skel-block"/>
      <div className="rec-body">
        <SkelLine w="35%" h={10}/>
        <SkelLine w="80%" h={16}/>
        <SkelLine w="60%" h={10}/>
        <div className="skel-block" style={{ height: 8, borderRadius: 999, marginTop: 10 }}/>
        <SkelLine w="90%" h={10}/>
      </div>
    </div>
  );
}

function SkelProfile() {
  return (
    <div className="profile-card skel">
      <SkelLine w="50%" h={18}/>
      <div style={{ display: "flex", gap: 10 }}>
        <SkelLine w="22%" h={22}/>
        <SkelLine w="22%" h={22}/>
        <SkelLine w="22%" h={22}/>
      </div>
      <SkelLine w="60%" h={8}/>
    </div>
  );
}

window.SkelLine = SkelLine;
window.SkelTile = SkelTile;
window.SkelRecCard = SkelRecCard;
window.SkelProfile = SkelProfile;
