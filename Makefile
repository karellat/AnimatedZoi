run:
	docker-compose up --remove-orphans --build --no-deps

stop:
	docker container prune -f

clean:
	docker image prune --all -f

test:
	curl http://localhost/predictions/drawn_humanoid_detector -F "data=@example/zoi.jpg" -o example/box.json
	python example/crop.py example/box.json example/zoi.jpg example/crop.png
	curl http://localhost/predictions/drawn_humanoid_pose_estimator -F "data=@example/crop.png" -o example/pose.json
	python example/pose.py example/pose.json example/crop.png example/chr_cfg.yaml
	curl -v http://localhost/render -F "motion_id=0" -F "char_cfg=@example/chr_cfg.yaml" -F "image=@example/crop.png" -o 'example/example0.gif'  
	curl -v http://localhost/render -F "motion_id=1" -F "char_cfg=@example/chr_cfg.yaml" -F "image=@example/crop.png" -o 'example/example1.gif'  
	curl -v http://localhost/render -F "motion_id=2" -F "char_cfg=@example/chr_cfg.yaml" -F "image=@example/crop.png" -o 'example/example2.gif'  
	curl -v http://localhost/render -F "motion_id=3" -F "char_cfg=@example/chr_cfg.yaml" -F "image=@example/crop.png" -o 'example/example3.gif'  
	curl -v http://localhost/render -F "motion_id=4" -F "char_cfg=@example/chr_cfg.yaml" -F "image=@example/crop.png" -o 'example/example4.gif'  
	curl -v http://localhost/render -F "motion_id=5" -F "char_cfg=@example/chr_cfg.yaml" -F "image=@example/crop.png" -o 'example/example5.gif'  
