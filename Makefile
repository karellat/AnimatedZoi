run: 
	sudo docker-compose up --remove-orphans --build
test:
	curl http://localhost/predictions/drawn_humanoid_detector -F "data=@example/zoi.jpg" -o example/box.json
	python example/crop.py example/box.json example/zoi.jpg example/crop.png
	curl http://localhost/predictions/drawn_humanoid_pose_estimator -F "data=@example/crop.png" -o example/pose.json
	python example/pose.py example/pose.json example/crop.png example/chr_cfg.yaml
	curl -v http://localhost/render -F "motion_id=1" -F "char_cfg=@example/chr_cfg.yaml" -F "image=@example/crop.png" -o 'example/example.gif'  