prepare_test:
	docker run --rm \
				-v ${PWD}:/host-pwd \
				-v ${PWD}/../swm:/host-swm \
				openapitools/openapi-generator-cli generate \
					-g python \
					-i /host-swm/priv/openapi.yaml \
					-o /host-pwd/test/mocked-server
