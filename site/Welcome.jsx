/* @jsx React.createElement */

function Welcome({ onChoose }) {
  return (
    <section className="welcome">
      <div className="welcome-art" aria-hidden="true">
        <img src={assetPath("/motifs/petal.svg")} className="welcome-petal welcome-petal-a" alt=""/>
        <img src={assetPath("/motifs/drop.svg")} className="welcome-petal welcome-petal-b" alt=""/>
        <img src={assetPath("/motifs/branch.svg")} className="welcome-branch" alt=""/>
      </div>
      <Eyebrow>A skincare studio, in software</Eyebrow>
      <h1 className="welcome-title">
        a soft start<br/>
        <em>for your shelf.</em>
      </h1>
      <p className="welcome-lede">
        Discover skincare you'll likely love — through the products you already adore, the ingredients in their neighborhood, and the model's confidence shown honestly.
      </p>
      <div className="welcome-actions">
        <PrimaryBtn onClick={() => onChoose("custom")}>Build my profile</PrimaryBtn>
        <SecondaryBtn onClick={() => onChoose("demo")}>Use a demo profile</SecondaryBtn>
      </div>
      <div className="welcome-foot">
        <span>Class-demo recommender · model + uncertainty served live from the FastAPI backend.</span>
      </div>
    </section>
  );
}

window.Welcome = Welcome;
