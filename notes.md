I couldn't find a paper that directly compares those two configurations (two equal small wheels vs a large front and smaller rear wheel). That looks like a genuine gap. But several studies come close, and together they support the idea that the *front* wheel matters most.

**The key study for your argument** is from Imperial College London (Posirisuk, Baker and Ghajari, published in *Accident Analysis & Prevention*). The researchers simulated riders on an e-scooter with 10in wheels at five different speeds over 12 differently sized potholes. They found no riders fell when the pothole was 3 cm deep (12% of wheel diameter), but at 6 cm deep (24% of wheel diameter), falls were predicted in 75% of cases for the smaller and average-sized riders. Crucially, the fall mechanism centres on the front wheel: the scooter rotates about the front wheel's axis after the wheel hits the far edge of the pothole. The authors concluded that wheel size and pothole depth need reconsidering from both design and road maintenance perspectives.

This framing helps your hypothesis a lot: if risk depends on pothole depth *relative to wheel diameter*, then a bigger front wheel makes the same pothole proportionally smaller, exactly where the fall begins.

**Front-rear asymmetry has been studied, but for tyres rather than wheel size.** A 2026 multibody dynamics study in *Machines* examined front and rear tyre stiffness separately. It notes in its background that larger-diameter wheels reduce vibration transmission and improve stability, and found that different inflation pressures front and rear gave the lowest vibration levels, recommending keeping the front wheel slightly above the rear. So researchers already treat front and rear as having different roles.

**Weaker but relevant evidence:** the scooter company Swifty ran practical pothole tests comparing a 16" big-wheeled scooter against an 8" model, the most common form factor on the market, finding that a 72mm-deep pothole was beyond the limit of the 8-inch scooter. Imperial's team even used a Swifty test to validate their model. But Swifty sells big-wheel scooters, so treat it as supporting evidence, not neutral research. Scooter patents also make the mechanical case: one argues a larger front wheel has a better angle of attack, so it's more likely to roll over an obstacle instead of getting stuck, and that it reduces the moment arm that pitches the rider over the handlebars. Patents aren't peer-reviewed, but they're useful for explaining the physics.

**What this means for your paper:** "Does a larger front wheel alone give most of the safety benefit?" is an original, focused question nobody seems to have answered. It also matters commercially, since a larger front wheel alone might be cheaper for operators like Voi than upsizing both. The Imperial model is the obvious foundation, and the authors at the Dyson School of Design Engineering would be excellent people to contact, since their paper explicitly calls for more work on wheel design.


That's a sensible hypothesis, and there's an even stronger reason to back it than weight distribution. But I'd treat the weight claim as something to *measure*, not assume, because it's less clear-cut than it feels.

**Weight distribution is more complicated than it seems.** When you ride steadily, your weight is spread across the deck, and the split depends on stance, rider height and the scooter's geometry. Many riders stand closer to the middle or even slightly back. Your point becomes much stronger during *deceleration*, though. Whenever you brake or hit something, momentum throws your weight forward onto the front wheel. And when the front wheel hits a pothole edge, it's suddenly decelerating, so the load on it spikes at exactly the worst moment. That's the mechanism in the Imperial study: the scooter pivots around the front axle and the rider gets thrown forward.

**The stronger argument is that the front wheel steers.** When the rear wheel hits a pothole, you get a jolt. When the front wheel hits one, you get a jolt *plus* a sudden twist of the handlebars, which can rip control away from the rider. A small front wheel catches more easily on edges and gets deflected more sharply. So the front wheel is where both the pitch-over risk and the loss-of-steering risk come from. That makes your "larger front wheel only" idea mechanically well-grounded, even if weight distribution alone doesn't settle it.

**You could test the weight question cheaply.** Put two bathroom scales under the scooter, one under each wheel, with the deck level, and stand in your normal riding position. The readings give you the static front/rear split. Repeat with a few friends of different heights. It's crude, but it's real data, and it would be a nice small section in your paper.

**Your sensor setup can also capture this.** The gyroscope on your handlebar mount can measure how sharply the bars twist on impact, which is a direct measure of the steering-loss risk. Comparing front-wheel impacts with rear-wheel impacts (you'll often see two spikes, a fraction of a second apart, as each wheel hits) could show that the first spike is the more dangerous one.

So I'd phrase your hypothesis something like: *"Because the front wheel both steers and bears the peak load during impact, increasing front wheel diameter alone yields most of the stability benefit of larger wheels."* That's specific, testable, and original.


Good question, and the honest answer is: he's worth contacting for one specific reason, but he's probably *not* the best person to help you publish.

**Why he's worth contacting**

Your modelling idea leans heavily on his group's finding about pothole depth relative to wheel diameter. But their simulations only used one wheel size (10 inches). Applying their thresholds to 8", 12" or 16" wheels, or to a bigger front wheel only, is an assumption you'd be making, and a reviewer would likely question it. His group is best placed to tell you whether that extrapolation is reasonable, or how to adjust it. That's a sharp, specific question, which is the kind busy academics actually answer. If he says it's sound, your paper becomes much stronger; if he says it isn't, you've avoided building on a shaky foundation.

**Why he's not your best publishing partner**

He's a senior researcher focused on brain injury, with a big lab, a fellowship and standards committee work. A cold email asking him to help publish a hobby paper is unlikely to get a yes, and his expertise is in what happens to the head after a fall, not in wheels, potholes or rider data. You'd also get more practical help from someone you can actually meet.

**Better options for each role**

For help publishing, someone in Oxford is better: a lecturer on your MSc (they know modelling and how to write it up) or a researcher at the Transport Studies Unit (they know transport journals and policy). Being in the same university makes a quick coffee chat realistic. For extending the engineering side, the authors of the 2026 *Machines* paper on front-rear tyre asymmetry are closer to your question, since they model scooter dynamics directly. If you contact Imperial at all, his former PhD students or co-authors, like Claire Baker, may be more likely to reply and can still answer your threshold question.

**My suggestion:** don't contact anyone at Imperial yet. Build your model first, then send one short email asking specifically whether their thresholds can be scaled to other wheel diameters. For mentorship and publishing, start in Oxford.
